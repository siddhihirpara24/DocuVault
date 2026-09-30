import re
import secrets
from datetime import datetime, timedelta
from flask import render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User, PasswordResetToken
from routes import auth_bp

def is_valid_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User Registration route."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Input Validations
        errors = []
        if not full_name:
            errors.append('Full Name is required.')
        if not email:
            errors.append('Email is required.')
        elif not is_valid_email(email):
            errors.append('Please provide a valid email address.')
        if not phone:
            errors.append('Phone number is required.')
        if not password:
            errors.append('Password is required.')
        elif len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Confirm password does not match.')

        # Check uniqueness of email
        if not errors:
            existing_user = User.query.filter_by(email=email).first()
            if existing_user:
                errors.append('An account with this email address already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('auth/register.html', full_name=full_name, email=email, phone=phone)

        # Create new user
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            role='user',
            status='active'
        )
        new_user.set_password(password)

        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! You can now log in with your credentials.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration. Please try again. ({str(e)})', 'danger')

    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User and Administrator Login route."""
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not email or not password:
            flash('Please enter both email and password.', 'warning')
            return render_template('auth/login.html', email=email)

        user = User.query.filter_by(email=email).first()

        # Check credentials and account status
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('auth/login.html', email=email)

        if user.status != 'active':
            flash('Your account has been deactivated. Please contact the administrator.', 'danger')
            return render_template('auth/login.html', email=email)

        # Log user in
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.full_name}!', 'success')

        # Role-based redirection
        next_page = request.args.get('next')
        if user.is_admin:
            return redirect(next_page or url_for('admin.dashboard'))
        else:
            return redirect(next_page or url_for('user.dashboard'))

    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password request route."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    demo_reset_url = None

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        if not email:
            flash('Please enter your email address.', 'warning')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()
        if not user:
            # For security reasons or college project demonstration:
            flash('If an account exists for this email, a password reset link has been generated.', 'info')
            return render_template('auth/forgot_password.html')

        # Clean old tokens for this user
        PasswordResetToken.query.filter_by(user_id=user.id).delete()

        # Generate new reset token (valid for 1 hour)
        token_string = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        reset_token = PasswordResetToken(user_id=user.id, token=token_string, expires_at=expires_at)

        try:
            db.session.add(reset_token)
            db.session.commit()

            demo_reset_url = url_for('auth.reset_password', token=token_string, _external=True)
            flash('Password reset link generated successfully! (In production this would be sent to your email)', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred. Please try again. ({str(e)})', 'danger')

    return render_template('auth/forgot_password.html', demo_reset_url=demo_reset_url)

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset completion route using secure token."""
    if current_user.is_authenticated:
        return redirect(url_for('user.dashboard'))

    token_record = PasswordResetToken.query.filter_by(token=token).first()
    if not token_record or not token_record.is_valid():
        flash('The password reset link is invalid or has expired. Please request a new one.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    user = token_record.user

    if request.method == 'POST':
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not new_password:
            flash('New password is required.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', token=token)

        # Update password
        user.set_password(new_password)
        # Delete token so it cannot be reused
        db.session.delete(token_record)

        try:
            db.session.commit()
            flash('Your password has been reset successfully! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred: {str(e)}', 'danger')

    return render_template('auth/reset_password.html', token=token, user_email=user.email)
