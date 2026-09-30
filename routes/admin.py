import io
import csv
from datetime import datetime, date, timedelta
from flask import render_template, request, redirect, url_for, flash, abort, Response, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from models import db, User, Category, Document
from routes import admin_bp
from utils.decorators import admin_required
from utils.helpers import delete_document_file

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin Dashboard with system metrics, Chart.js analytics, recent users and documents."""
    total_users = User.query.filter_by(role='user').count()
    active_users = User.query.filter_by(role='user', status='active').count()
    total_documents = Document.query.count()
    total_categories = Category.query.count()

    # Documents uploaded today
    today_start = datetime.combine(date.today(), datetime.min.time())
    docs_today = Document.query.filter(Document.upload_date >= today_start).count()

    # Recent 5 users
    recent_users = User.query.filter_by(role='user').order_by(User.created_at.desc()).limit(5).all()

    # Recent 5 documents across all users
    recent_documents = Document.query.order_by(Document.upload_date.desc()).limit(5).all()

    # Chart Data: Documents by Category
    cat_stats = db.session.query(
        Category.name,
        func.count(Document.id)
    ).outerjoin(Document, Category.id == Document.category_id)\
     .group_by(Category.id, Category.name)\
     .all()

    cat_labels = [c[0] for c in cat_stats]
    cat_counts = [c[1] for c in cat_stats]

    # Chart Data: Documents by File Type
    type_stats = db.session.query(
        Document.file_type,
        func.count(Document.id)
    ).group_by(Document.file_type).all()

    type_labels = [t[0] for t in type_stats] if type_stats else ['None']
    type_counts = [t[1] for t in type_stats] if type_stats else [0]

    # Chart Data: Uploads per month (last 6 months)
    monthly_stats = []
    month_labels = []
    month_counts = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        # Calculate start and end of target month
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_start = datetime(year, month, 1)
        if month == 12:
            m_end = datetime(year + 1, 1, 1)
        else:
            m_end = datetime(year, month + 1, 1)
        
        count = Document.query.filter(Document.upload_date >= m_start, Document.upload_date < m_end).count()
        month_labels.append(m_start.strftime('%b %Y'))
        month_counts.append(count)

    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'total_documents': total_documents,
        'total_categories': total_categories,
        'docs_today': docs_today
    }

    chart_data = {
        'cat_labels': cat_labels,
        'cat_counts': cat_counts,
        'type_labels': type_labels,
        'type_counts': type_counts,
        'month_labels': month_labels,
        'month_counts': month_counts
    }

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        recent_users=recent_users,
        recent_documents=recent_documents,
        chart_data=chart_data
    )

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """Admin Manage Users page."""
    search_query = request.args.get('q', '').strip()
    status_filter = request.args.get('status', '').strip()

    query = User.query.filter(User.role != 'admin')

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            (User.full_name.ilike(like_pattern)) |
            (User.email.ilike(like_pattern)) |
            (User.phone.ilike(like_pattern))
        )

    if status_filter in ['active', 'inactive']:
        query = query.filter_by(status=status_filter)

    all_users = query.order_by(User.created_at.desc()).all()

    return render_template(
        'admin/users.html',
        users=all_users,
        search_query=search_query,
        status_filter=status_filter
    )

@admin_bp.route('/users/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    """View detailed user information and their uploaded documents."""
    user = User.query.get_or_404(user_id)
    user_documents = Document.query.filter_by(user_id=user.id).order_by(Document.upload_date.desc()).all()
    return render_template('admin/user_details.html', user=user, documents=user_documents)

@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_user_status(user_id):
    """Activate or deactivate a user account."""
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash('You cannot change your own admin account status.', 'danger')
        return redirect(url_for('admin.users'))

    user.status = 'inactive' if user.status == 'active' else 'active'
    user.updated_at = datetime.utcnow()

    try:
        db.session.commit()
        status_text = 'activated' if user.status == 'active' else 'deactivated'
        flash(f'User "{user.full_name}" has been {status_text}.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    """Safely delete a user account and purge all their uploaded physical files."""
    user = User.query.get_or_404(user_id)

    # Protect current admin account
    if user.id == current_user.id:
        flash('Action Denied: You cannot delete your own active administrator account.', 'danger')
        return redirect(url_for('admin.users'))

    try:
        # Purge all physical document files belonging to this user
        user_docs = Document.query.filter_by(user_id=user.id).all()
        for doc in user_docs:
            delete_document_file(doc.file_path)

        # Delete database user record (cascading deletes documents & tokens)
        db.session.delete(user)
        db.session.commit()

        flash(f'User "{user.full_name}" and all associated documents were deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred while deleting user: {str(e)}', 'danger')

    return redirect(url_for('admin.users'))

@admin_bp.route('/documents')
@login_required
@admin_required
def documents():
    """Admin Manage Documents page with system-wide search and filters."""
    search_query = request.args.get('q', '').strip()
    user_id = request.args.get('user', type=int)
    category_id = request.args.get('category', type=int)
    file_type = request.args.get('file_type', '').strip().upper()
    date_filter = request.args.get('date', '').strip()

    query = Document.query

    if search_query:
        like_pattern = f"%{search_query}%"
        query = query.filter(
            (Document.document_name.ilike(like_pattern)) |
            (Document.description.ilike(like_pattern)) |
            (Document.original_filename.ilike(like_pattern))
        )

    if user_id:
        query = query.filter(Document.user_id == user_id)

    if category_id:
        query = query.filter(Document.category_id == category_id)

    if file_type:
        query = query.filter(Document.file_type == file_type)

    if date_filter:
        try:
            target_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            d_start = datetime.combine(target_date, datetime.min.time())
            d_end = datetime.combine(target_date, datetime.max.time())
            query = query.filter(Document.upload_date >= d_start, Document.upload_date <= d_end)
        except ValueError:
            pass

    all_docs = query.order_by(Document.upload_date.desc()).all()
    categories = Category.query.order_by(Category.name).all()
    users_list = User.query.filter_by(role='user').order_by(User.full_name).all()
    file_types = ['PDF', 'JPG', 'PNG', 'DOC', 'DOCX']

    return render_template(
        'admin/documents.html',
        documents=all_docs,
        categories=categories,
        users_list=users_list,
        file_types=file_types,
        search_query=search_query,
        selected_user=user_id,
        selected_category=category_id,
        selected_file_type=file_type,
        date_filter=date_filter
    )

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    """Admin Manage Categories page."""
    all_categories = Category.query.order_by(Category.name).all()

    # Precalculate document counts
    categories_data = []
    for cat in all_categories:
        count = Document.query.filter_by(category_id=cat.id).count()
        categories_data.append({
            'category': cat,
            'count': count
        })

    return render_template('admin/categories.html', categories_data=categories_data)

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    """Create a new document category."""
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category Name cannot be empty.', 'danger')
        return redirect(url_for('admin.categories'))

    existing = Category.query.filter(Category.name.ilike(name)).first()
    if existing:
        flash(f'Category "{name}" already exists.', 'warning')
        return redirect(url_for('admin.categories'))

    new_cat = Category(name=name, description=description)
    try:
        db.session.add(new_cat)
        db.session.commit()
        flash(f'Category "{name}" added successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'danger')

    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/<int:cat_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_category(cat_id):
    """Edit existing category name and description."""
    category = Category.query.get_or_404(cat_id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    if not name:
        flash('Category Name cannot be empty.', 'danger')
        return redirect(url_for('admin.categories'))

    existing = Category.query.filter(Category.name.ilike(name), Category.id != cat_id).first()
    if existing:
        flash(f'Another category named "{name}" already exists.', 'warning')
        return redirect(url_for('admin.categories'))

    category.name = name
    category.description = description

    try:
        db.session.commit()
        flash('Category updated successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'danger')

    return redirect(url_for('admin.categories'))

@admin_bp.route('/categories/<int:cat_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(cat_id):
    """Delete a category with confirmation check for linked documents."""
    category = Category.query.get_or_404(cat_id)
    doc_count = Document.query.filter_by(category_id=category.id).count()

    reassign_to_other = bool(request.form.get('reassign_to_other'))

    try:
        if doc_count > 0:
            if reassign_to_other:
                # Find or create 'Other' category
                other_cat = Category.query.filter(Category.name.ilike('Other')).first()
                if not other_cat:
                    other_cat = Category(name='Other', description='Uncategorized documents')
                    db.session.add(other_cat)
                    db.session.commit()
                # Reassign documents
                Document.query.filter_by(category_id=category.id).update({'category_id': other_cat.id})
                db.session.commit()
            else:
                # Remove category association (category_id becomes NULL)
                Document.query.filter_by(category_id=category.id).update({'category_id': None})
                db.session.commit()

        db.session.delete(category)
        db.session.commit()
        flash(f'Category "{category.name}" was deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'danger')

    return redirect(url_for('admin.categories'))

@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    """Admin Reports page with comprehensive breakdown and print view."""
    total_users = User.query.filter_by(role='user').count()
    active_users = User.query.filter_by(role='user', status='active').count()
    total_docs = Document.query.count()

    # Category breakdown
    cat_data = db.session.query(
        Category.name,
        func.count(Document.id)
    ).outerjoin(Document, Category.id == Document.category_id)\
     .group_by(Category.id, Category.name)\
     .order_by(func.count(Document.id).desc())\
     .all()

    # Most used category
    most_used_category = cat_data[0][0] if cat_data and cat_data[0][1] > 0 else 'N/A'

    # File type breakdown
    type_data = db.session.query(
        Document.file_type,
        func.count(Document.id),
        func.sum(Document.file_size)
    ).group_by(Document.file_type)\
     .order_by(func.count(Document.id).desc())\
     .all()

    # Monthly upload statistics
    monthly_data = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        year = now.year
        month = now.month - i
        while month <= 0:
            month += 12
            year -= 1
        m_start = datetime(year, month, 1)
        if month == 12:
            m_end = datetime(year + 1, 1, 1)
        else:
            m_end = datetime(year, month + 1, 1)
        
        count = Document.query.filter(Document.upload_date >= m_start, Document.upload_date < m_end).count()
        monthly_data.append({
            'month': m_start.strftime('%B %Y'),
            'count': count
        })

    return render_template(
        'admin/reports.html',
        total_users=total_users,
        active_users=active_users,
        total_docs=total_docs,
        most_used_category=most_used_category,
        cat_data=cat_data,
        type_data=type_data,
        monthly_data=monthly_data
    )

@admin_bp.route('/reports/export-csv')
@login_required
@admin_required
def export_csv():
    """Export all document records as a downloadable CSV file."""
    output = io.StringIO()
    writer = csv.writer(output)

    # Write CSV Header
    writer.writerow([
        'Document ID', 'Document Name', 'User Name', 'User Email',
        'Category', 'File Type', 'File Size (Bytes)', 'Upload Date', 'Description'
    ])

    # Write Data Rows
    documents = Document.query.order_by(Document.upload_date.desc()).all()
    for doc in documents:
        writer.writerow([
            doc.id,
            doc.document_name,
            doc.user.full_name if doc.user else 'Unknown',
            doc.user.email if doc.user else 'Unknown',
            doc.category.name if doc.category else 'Uncategorized',
            doc.file_type,
            doc.file_size,
            doc.upload_date.strftime('%Y-%m-%d %H:%M:%S'),
            doc.description or ''
        ])

    csv_data = output.getvalue()
    filename = f"document_organizer_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

@admin_bp.route('/profile', methods=['GET', 'POST'])
@login_required
@admin_required
def profile():
    """Admin profile management."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not full_name:
            flash('Full Name cannot be empty.', 'danger')
            return render_template('admin/profile.html')

        current_user.full_name = full_name
        current_user.phone = phone
        current_user.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            flash('Admin profile updated successfully.', 'success')
            return redirect(url_for('admin.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('admin/profile.html')
