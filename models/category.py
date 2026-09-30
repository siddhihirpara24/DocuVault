from datetime import datetime
from models import db

class Category(db.Model):
    """Category model for classifying documents."""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Database relationships
    documents = db.relationship('Document', back_populates='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'
