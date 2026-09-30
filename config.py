import os
from dotenv import load_dotenv

# Base directory of the project
basedir = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base application configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super-secret-default-dev-key-change-me'
    
    # Database Configuration
    # Defaults to MySQL if configured, with graceful fallback to SQLite for local development
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        DATABASE_URL = f"sqlite:///{os.path.join(basedir, 'database', 'document_organizer.db')}"
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads Configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 10 * 1024 * 1024))  # 10 MB maximum
    ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
    
    # Security & Session Settings
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_DURATION = 86400 * 14  # 14 days
    WTF_CSRF_ENABLED = True
