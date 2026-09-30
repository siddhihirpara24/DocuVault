import os
from datetime import datetime
from flask import render_template, request, redirect, url_for, flash, abort, send_file, current_app
from flask_login import login_required, current_user
from models import db, User, Category, Document
from routes import user_bp
from utils.helpers import allowed_file, save_document_file, delete_document_file

@user_bp.route('/')
@user_bp.route('/dashboard')
@login_required
def dashboard():
    """User Dashboard displaying statistics cards, quick actions, and recent documents."""
    user_id = current_user.id

    # Compute category statistics
    total_docs = Document.query.filter_by(user_id=user_id).count()

    # Query counts for specific key categories
    education_cat = Category.query.filter(Category.name.ilike('education')).first()
    identity_cat = Category.query.filter(Category.name.ilike('identity')).first()
    career_cat = Category.query.filter(Category.name.ilike('career')).first()

    education_count = Document.query.filter_by(user_id=user_id, category_id=education_cat.id).count() if education_cat else 0
    identity_count = Document.query.filter_by(user_id=user_id, category_id=identity_cat.id).count() if identity_cat else 0
    career_count = Document.query.filter_by(user_id=user_id, category_id=career_cat.id).count() if career_cat else 0
    
    # Calculate count for "Other" or non-major categories
    major_cat_ids = [c.id for c in [education_cat, identity_cat, career_cat] if c]
    other_count = Document.query.filter(
        Document.user_id == user_id,
        ~Document.category_id.in_(major_cat_ids) if major_cat_ids else True
    ).count()

    # Fetch 6 most recently uploaded documents
    recent_docs = Document.query.filter_by(user_id=user_id)\
        .order_by(Document.upload_date.desc())\
        .limit(6)\
        .all()

    stats = {
        'total': total_docs,
        'education': education_count,
        'identity': identity_count,
        'career': career_count,
        'other': other_count
    }

    return render_template('user/dashboard.html', stats=stats, recent_docs=recent_docs)

@user_bp.route('/documents')
@login_required
def documents():
    """Display all documents belonging strictly to the logged-in user with optional category filtering."""
    category_id = request.args.get('category', type=int)
    category_name = request.args.get('category_name', type=str)

    query = Document.query.filter_by(user_id=current_user.id)

    selected_category = None
    if category_id:
        query = query.filter_by(category_id=category_id)
        selected_category = db.session.get(Category, category_id)
    elif category_name:
        selected_category = Category.query.filter(Category.name.ilike(category_name)).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)

    user_documents = query.order_by(Document.upload_date.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    return render_template(
        'user/documents.html',
        documents=user_documents,
        categories=categories,
        selected_category=selected_category
    )

@user_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload Document page and processing."""
    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        document_name = request.form.get('document_name', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        file = request.files.get('document_file')

        # Form Validations
        errors = []
        if not document_name:
            errors.append('Document Name is required.')

        if not category_id:
            errors.append('Please select a valid document category.')

        if not file or file.filename == '':
            errors.append('Please select a file to upload.')
        elif not allowed_file(file.filename):
            errors.append('Invalid file format. Allowed types: PDF, JPG, JPEG, PNG, DOC, DOCX.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('user/upload.html', categories=categories,
                                   document_name=document_name, category_id=category_id,
                                   description=description)

        try:
            # Save file to uploads folder
            file_meta = save_document_file(file, current_app.config['UPLOAD_FOLDER'])

            # Store document record in MySQL / DB
            document = Document(
                user_id=current_user.id,
                category_id=category_id,
                document_name=document_name,
                description=description,
                original_filename=file_meta['original_filename'],
                stored_filename=file_meta['stored_filename'],
                file_path=file_meta['file_path'],
                file_type=file_meta['file_type'],
                file_size=file_meta['file_size']
            )

            db.session.add(document)
            db.session.commit()

            flash('Document uploaded successfully.', 'success')
            return redirect(url_for('user.documents'))

        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while uploading document: {str(e)}', 'danger')

    return render_template('user/upload.html', categories=categories)

@user_bp.route('/document/<int:doc_id>')
@user_bp.route('/document/<int:doc_id>/view')
@login_required
def view_document(doc_id):
    """View Document details and in-browser preview."""
    document = Document.query.get_or_404(doc_id)

    # Strict authorization check: Only owner or admin can view
    if document.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access: You do not have permission to view this document.', 'danger')
        abort(403)

    return render_template('user/view_document.html', document=document)

@user_bp.route('/document/<int:doc_id>/file')
@login_required
def stream_file(doc_id):
    """Serve document file for in-browser viewing or embedding."""
    document = Document.query.get_or_404(doc_id)

    # Strict authorization check
    if document.user_id != current_user.id and not current_user.is_admin:
        abort(403)

    if not os.path.exists(document.file_path):
        flash('The requested file could not be found on the server storage.', 'danger')
        abort(404)

    # In-browser streaming
    return send_file(document.file_path, as_attachment=False, download_name=document.original_filename)

@user_bp.route('/document/<int:doc_id>/download')
@login_required
def download_document(doc_id):
    """Securely download document file with its original filename."""
    document = Document.query.get_or_404(doc_id)

    # Strict authorization check
    if document.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access: You do not have permission to download this document.', 'danger')
        abort(403)

    if not os.path.exists(document.file_path):
        flash('File not found on storage server.', 'danger')
        return redirect(url_for('user.documents'))

    return send_file(
        document.file_path,
        as_attachment=True,
        download_name=document.original_filename
    )

@user_bp.route('/document/<int:doc_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(doc_id):
    """Edit document metadata and optionally replace the file."""
    document = Document.query.get_or_404(doc_id)

    # Strict authorization check
    if document.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access: You do not have permission to edit this document.', 'danger')
        abort(403)

    categories = Category.query.order_by(Category.name).all()

    if request.method == 'POST':
        document_name = request.form.get('document_name', '').strip()
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        replacement_file = request.files.get('document_file')

        if not document_name:
            flash('Document Name is required.', 'danger')
            return render_template('user/edit_document.html', document=document, categories=categories)

        document.document_name = document_name
        document.category_id = category_id
        document.description = description
        document.updated_at = datetime.utcnow()

        # Handle optional replacement file
        if replacement_file and replacement_file.filename != '':
            if not allowed_file(replacement_file.filename):
                flash('Invalid file format. Allowed types: PDF, JPG, JPEG, PNG, DOC, DOCX.', 'danger')
                return render_template('user/edit_document.html', document=document, categories=categories)

            # Delete old physical file safely
            delete_document_file(document.file_path)

            # Save replacement file
            file_meta = save_document_file(replacement_file, current_app.config['UPLOAD_FOLDER'])
            document.original_filename = file_meta['original_filename']
            document.stored_filename = file_meta['stored_filename']
            document.file_path = file_meta['file_path']
            document.file_type = file_meta['file_type']
            document.file_size = file_meta['file_size']

        try:
            db.session.commit()
            flash('Document updated successfully.', 'success')
            return redirect(url_for('user.documents'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating document: {str(e)}', 'danger')

    return render_template('user/edit_document.html', document=document, categories=categories)

@user_bp.route('/document/<int:doc_id>/delete', methods=['POST'])
@login_required
def delete_document(doc_id):
    """Delete document record and physical file from server."""
    document = Document.query.get_or_404(doc_id)

    # Strict authorization check
    if document.user_id != current_user.id and not current_user.is_admin:
        flash('Unauthorized access: You do not have permission to delete this document.', 'danger')
        abort(403)

    try:
        # Delete physical file
        delete_document_file(document.file_path)

        # Delete database record
        db.session.delete(document)
        db.session.commit()

        flash('Document deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting document: {str(e)}', 'danger')

    # If an admin triggered this from admin panel, redirect to admin documents
    if request.referrer and '/admin/' in request.referrer:
        return redirect(url_for('admin.documents'))
    return redirect(url_for('user.documents'))

@user_bp.route('/search')
@login_required
def search():
    """Search and filter user's documents by name, description, category, and file format."""
    query_str = request.args.get('q', '').strip()
    category_id = request.args.get('category', type=int)
    file_type = request.args.get('file_type', '').strip().upper()

    base_query = Document.query.filter_by(user_id=current_user.id)

    # Text search in name or description
    if query_str:
        like_pattern = f"%{query_str}%"
        base_query = base_query.filter(
            (Document.document_name.ilike(like_pattern)) |
            (Document.description.ilike(like_pattern)) |
            (Document.original_filename.ilike(like_pattern))
        )

    # Filter by category
    if category_id:
        base_query = base_query.filter(Document.category_id == category_id)

    # Filter by file type
    if file_type:
        base_query = base_query.filter(Document.file_type == file_type)

    results = base_query.order_by(Document.upload_date.desc()).all()
    categories = Category.query.order_by(Category.name).all()

    # Distinct file types available for filtering
    file_types = ['PDF', 'JPG', 'PNG', 'DOC', 'DOCX']

    return render_template(
        'user/search.html',
        results=results,
        categories=categories,
        file_types=file_types,
        query_str=query_str,
        selected_category=category_id,
        selected_file_type=file_type
    )

@user_bp.route('/categories')
@login_required
def categories():
    """Display all categories with dynamic count of documents uploaded by the user."""
    all_categories = Category.query.order_by(Category.name).all()

    categories_data = []
    for cat in all_categories:
        count = Document.query.filter_by(user_id=current_user.id, category_id=cat.id).count()
        categories_data.append({
            'category': cat,
            'count': count
        })

    return render_template('user/categories.html', categories_data=categories_data)

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile management."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not full_name:
            flash('Full Name cannot be empty.', 'danger')
            return render_template('user/profile.html')

        current_user.full_name = full_name
        current_user.phone = phone
        current_user.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash('Profile updated successfully.', 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while updating profile: {str(e)}', 'danger')

    doc_count = Document.query.filter_by(user_id=current_user.id).count()
    return render_template('user/profile.html', doc_count=doc_count)

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change user password."""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '')
        new_password = request.form.get('new_password', '')
        confirm_new_password = request.form.get('confirm_new_password', '')

        # Validations
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'danger')
            return render_template('user/change_password.html')

        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'danger')
            return render_template('user/change_password.html')

        if new_password != confirm_new_password:
            flash('New password confirmation does not match.', 'danger')
            return render_template('user/change_password.html')

        # Update password
        current_user.set_password(new_password)
        current_user.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash('Password changed successfully.', 'success')
            return redirect(url_for('user.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('user/change_password.html')
