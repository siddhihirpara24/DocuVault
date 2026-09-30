from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from models import db

class User(db.Model, UserMixin):
    """User model representing application users and administrators."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)  # 'user' or 'admin'
    status = db.Column(db.String(20), default='active', nullable=False)  # 'active' or 'inactive'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Database relationships
    documents = db.relationship('Document', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')
    password_reset_tokens = db.relationship('PasswordResetToken', back_populates='user', cascade='all, delete-orphan', lazy='dynamic')

    def set_password(self, password):
        """Hash and store the user's password securely."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the password against the stored secure hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        """Check if the user has administrator privileges."""
        return self.role == 'admin'

    @property
    def is_active(self):
        """Flask-Login property: only active users can authenticate."""
        return self.status == 'active'

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'
