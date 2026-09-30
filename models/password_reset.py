from datetime import datetime
from models import db

class PasswordResetToken(db.Model):
    """Model to store temporary tokens for password reset flow."""
    __tablename__ = 'password_reset_tokens'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='password_reset_tokens')

    def is_valid(self):
        """Check if the token has not expired."""
        return datetime.utcnow() < self.expires_at

    def __repr__(self):
        return f'<PasswordResetToken user_id={self.user_id}>'
