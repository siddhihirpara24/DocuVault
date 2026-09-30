from flask import Blueprint

# Initialize Blueprints
auth_bp = Blueprint('auth', __name__)
user_bp = Blueprint('user', __name__)
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Import route handlers to register endpoints
from routes import auth, user, admin

__all__ = ['auth_bp', 'user_bp', 'admin_bp']
