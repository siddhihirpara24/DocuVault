import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_login import LoginManager, current_user
from config import Config
from models import db, User, Category
from routes import auth_bp, user_bp, admin_bp

def create_app(config_class=Config):
    """Application factory for Personal Document Organizer."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure uploads directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'database'), exist_ok=True)

    # Database initialization with graceful fallback if MySQL is not yet created/connected
    try:
        from sqlalchemy import create_engine
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        with engine.connect() as conn:
            pass
    except Exception as e:
        # If MySQL connection fails, fallback to local SQLite so application always runs out of the box
        sqlite_fallback = f"sqlite:///{os.path.join(app.root_path, 'database', 'document_organizer.db')}"
        print(f"[Database Notice] Could not connect to configured DATABASE_URL: {e}")
        print(f"[Database Notice] Falling back gracefully to SQLite: {sqlite_fallback}")
        app.config['SQLALCHEMY_DATABASE_URI'] = sqlite_fallback

    # Initialize extensions
    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'warning'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)

    # Root route redirect
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            if current_user.is_admin:
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('user.dashboard'))
        return redirect(url_for('auth.login'))

    # Global context processors for templates
    @app.context_processor
    def inject_global_data():
        from datetime import datetime
        return {
            'current_year': datetime.utcnow().year,
            'app_name': 'DocuVault',
            'app_title': 'Personal Document Organizer'
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(error):
        flash('File size exceeds the allowable limit of 10 MB. Please upload a smaller file.', 'danger')
        return redirect(request.referrer or url_for('user.dashboard'))

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

# Main entry point instance
app = create_app()

if __name__ == '__main__':
    # Automatically create tables if they do not exist
    with app.app_context():
        db.create_all()
    # Run development server
    app.run(debug=True, host='0.0.0.0', port=5000)
