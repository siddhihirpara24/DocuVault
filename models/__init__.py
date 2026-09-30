from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy instance
db = SQLAlchemy()

# Import models for easy access across the application
from models.user import User
from models.category import Category
from models.document import Document
from models.password_reset import PasswordResetToken

__all__ = ['db', 'User', 'Category', 'Document', 'PasswordResetToken']
