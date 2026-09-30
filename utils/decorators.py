from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user

def admin_required(f):
    """
    Decorator to ensure that the current logged in user has administrative privileges.
    If unauthenticated or not an admin, access is denied with a 403 status or redirect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in with an administrator account to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access Denied: You do not have administrator permissions.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
