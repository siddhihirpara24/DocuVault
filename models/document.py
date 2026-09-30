from datetime import datetime
from models import db

class Document(db.Model):
    """Document model representing user-uploaded files and their metadata."""
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True, index=True)
    document_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), unique=True, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)  # PDF, JPG, PNG, DOC, DOCX, etc.
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', back_populates='documents')
    category = db.relationship('Category', back_populates='documents')

    @property
    def formatted_file_size(self):
        """Format file size in bytes to human-readable string."""
        if not self.file_size:
            return '0 B'
        size = float(self.file_size)
        units = ['B', 'KB', 'MB', 'GB']
        for unit in units:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    @property
    def is_previewable_pdf(self):
        """Return True if document is a PDF previewable in browser."""
        return self.file_type.lower() == 'pdf'

    @property
    def is_previewable_image(self):
        """Return True if document is an image previewable in browser."""
        return self.file_type.lower() in ['jpg', 'jpeg', 'png', 'webp']

    @property
    def is_previewable(self):
        """Return True if document can be rendered inline."""
        return self.is_previewable_pdf or self.is_previewable_image

    @property
    def file_icon(self):
        """Return Bootstrap icon class based on file type."""
        ext = self.file_type.lower()
        if ext == 'pdf':
            return 'bi-file-earmark-pdf-fill text-danger'
        elif ext in ['jpg', 'jpeg', 'png', 'webp']:
            return 'bi-file-earmark-image-fill text-primary'
        elif ext in ['doc', 'docx']:
            return 'bi-file-earmark-word-fill text-info'
        return 'bi-file-earmark-text-fill text-secondary'

    def __repr__(self):
        return f'<Document {self.document_name} ({self.file_type})>'
