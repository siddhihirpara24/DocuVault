import os
import uuid
from werkzeug.utils import secure_filename
from config import Config

def allowed_file(filename):
    """
    Check if the provided filename has an extension allowed by system configuration.
    Allowed extensions: PDF, JPG, JPEG, PNG, DOC, DOCX
    """
    if not filename or '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def get_file_type(filename):
    """Return uppercase file extension (e.g. 'PDF', 'PNG', 'DOCX')."""
    if not filename or '.' not in filename:
        return 'UNKNOWN'
    return filename.rsplit('.', 1)[1].upper()

def save_document_file(file_storage, upload_folder):
    """
    Save an uploaded file safely with a unique filename to prevent collisions.
    Returns a dictionary containing metadata:
    - original_filename
    - stored_filename
    - file_path
    - file_type
    - file_size
    """
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder, exist_ok=True)

    original_filename = file_storage.filename
    clean_filename = secure_filename(original_filename)
    if not clean_filename:
        clean_filename = "document"

    file_extension = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else 'bin'
    
    # Generate unique stored filename
    unique_prefix = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_prefix}_{clean_filename}"
    file_path = os.path.join(upload_folder, stored_filename)

    # Save the physical file
    file_storage.save(file_path)

    # Get file size in bytes
    file_size = os.path.getsize(file_path)

    return {
        'original_filename': original_filename,
        'stored_filename': stored_filename,
        'file_path': file_path,
        'file_type': file_extension.upper(),
        'file_size': file_size
    }

def delete_document_file(file_path):
    """Safely delete physical file from server storage."""
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        # Log or quietly handle deletion errors without failing DB operations
        print(f"Warning: Failed to delete physical file {file_path}: {e}")
    return False
