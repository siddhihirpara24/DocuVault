import os
import uuid
from typing import List, Optional
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from config import Config, basedir
from models import User, Category, Document, PasswordResetToken
from utils.helpers import allowed_file, delete_document_file

# Initialize FastAPI Application
app = FastAPI(
    title="DocuVault - Personal Document Organizer REST API",
    description="Full-featured RESTful API powered by **FastAPI** and **SQLAlchemy** with automatic interactive OpenAPI / Swagger documentation.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enable CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database Setup for FastAPI
db_uri = Config.SQLALCHEMY_DATABASE_URI
try:
    test_engine = create_engine(db_uri)
    with test_engine.connect():
        pass
except Exception:
    db_uri = f"sqlite:///{os.path.join(basedir, 'database', 'document_organizer.db')}"

engine = create_engine(
    db_uri,
    connect_args={"check_same_thread": False} if "sqlite" in db_uri else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that provides a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------
# Pydantic Schemas for Request & Response Serialization
# -------------------------------------------------------------

class UserRegisterSchema(BaseModel):
    full_name: str = Field(..., example="Alex Johnson")
    email: EmailStr = Field(..., example="alex@example.com")
    phone: str = Field(..., example="+1 234 567 8900")
    password: str = Field(..., min_length=6, example="Secret123")

class UserLoginSchema(BaseModel):
    email: EmailStr = Field(..., example="admin@gmail.com")
    password: str = Field(..., example="Admin@123")

class UserResponseSchema(BaseModel):
    id: int
    full_name: str
    email: str
    phone: Optional[str] = None
    role: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class CategoryResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    created_at: datetime
    document_count: Optional[int] = 0

    class Config:
        from_attributes = True

class CategoryCreateSchema(BaseModel):
    name: str = Field(..., example="Real Estate")
    description: Optional[str] = Field(None, example="Property deeds and lease documents")

class DocumentResponseSchema(BaseModel):
    id: int
    user_id: int
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    document_name: str
    description: Optional[str] = None
    original_filename: str
    file_type: str
    file_size: int
    formatted_file_size: str
    upload_date: datetime

    class Config:
        from_attributes = True

class DocumentUpdateSchema(BaseModel):
    document_name: Optional[str] = None
    category_id: Optional[int] = None
    description: Optional[str] = None

class DashboardStatsSchema(BaseModel):
    total_users: int
    total_documents: int
    total_categories: int
    categories_breakdown: List[dict]
    file_types_breakdown: List[dict]

# -------------------------------------------------------------
# Root & Health Endpoints
# -------------------------------------------------------------

@app.get("/", include_in_schema=False)
def root():
    """Redirect root visitors to the interactive Swagger UI."""
    return RedirectResponse(url="/docs")

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint to verify API server status."""
    return {
        "status": "healthy",
        "service": "DocuVault FastAPI",
        "timestamp": datetime.utcnow().isoformat()
    }

# -------------------------------------------------------------
# Authentication & User Endpoints
# -------------------------------------------------------------

@app.post("/api/auth/register", response_model=UserResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Authentication"])
def register_user(payload: UserRegisterSchema, db: Session = Depends(get_db)):
    """Register a new user account via REST API."""
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email is already registered.")

    new_user = User(
        full_name=payload.full_name,
        email=payload.email.lower(),
        phone=payload.phone,
        role="user",
        status="active"
    )
    new_user.set_password(payload.password)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/auth/login", tags=["Authentication"])
def login_user(payload: UserLoginSchema, db: Session = Depends(get_db)):
    """Authenticate user credentials and return profile metadata."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not user.check_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is deactivated.")

    return {
        "status": "success",
        "message": f"Welcome back, {user.full_name}!",
        "user": {
            "id": user.id,
            "full_name": user.full_name,
            "email": user.email,
            "role": user.role
        }
    }

@app.get("/api/users", response_model=List[UserResponseSchema], tags=["Users"])
def get_all_users(db: Session = Depends(get_db)):
    """List all registered users (Admin access)."""
    return db.query(User).all()

# -------------------------------------------------------------
# Category Endpoints
# -------------------------------------------------------------

@app.get("/api/categories", response_model=List[CategoryResponseSchema], tags=["Categories"])
def get_categories(db: Session = Depends(get_db)):
    """Fetch all document categories with associated file counts."""
    categories = db.query(Category).all()
    result = []
    for cat in categories:
        doc_count = db.query(Document).filter(Document.category_id == cat.id).count()
        result.append(CategoryResponseSchema(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            created_at=cat.created_at,
            document_count=doc_count
        ))
    return result

@app.post("/api/categories", response_model=CategoryResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Categories"])
def create_category(payload: CategoryCreateSchema, db: Session = Depends(get_db)):
    """Create a new document category."""
    existing = db.query(Category).filter(Category.name.ilike(payload.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Category '{payload.name}' already exists.")

    new_cat = Category(name=payload.name, description=payload.description)
    db.add(new_cat)
    db.commit()
    db.refresh(new_cat)
    return new_cat

# -------------------------------------------------------------
# Document Management Endpoints
# -------------------------------------------------------------

@app.get("/api/documents", response_model=List[DocumentResponseSchema], tags=["Documents"])
def get_documents(
    user_id: Optional[int] = Query(None, description="Filter by User ID"),
    category_id: Optional[int] = Query(None, description="Filter by Category ID"),
    q: Optional[str] = Query(None, description="Search keyword in name or description"),
    file_type: Optional[str] = Query(None, description="Filter by file type (e.g. PDF, PNG)"),
    db: Session = Depends(get_db)
):
    """Retrieve documents with multifaceted query filters."""
    query = db.query(Document)

    if user_id:
        query = query.filter(Document.user_id == user_id)
    if category_id:
        query = query.filter(Document.category_id == category_id)
    if file_type:
        query = query.filter(Document.file_type == file_type.upper())
    if q:
        like_pattern = f"%{q}%"
        query = query.filter(
            (Document.document_name.ilike(like_pattern)) |
            (Document.description.ilike(like_pattern)) |
            (Document.original_filename.ilike(like_pattern))
        )

    docs = query.order_by(Document.upload_date.desc()).all()
    results = []
    for doc in docs:
        results.append(DocumentResponseSchema(
            id=doc.id,
            user_id=doc.user_id,
            category_id=doc.category_id,
            category_name=doc.category.name if doc.category else None,
            document_name=doc.document_name,
            description=doc.description,
            original_filename=doc.original_filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            formatted_file_size=doc.formatted_file_size,
            upload_date=doc.upload_date
        ))
    return results

@app.post("/api/documents/upload", response_model=DocumentResponseSchema, status_code=status.HTTP_201_CREATED, tags=["Documents"])
async def upload_document(
    user_id: int = Form(...),
    category_id: int = Form(...),
    document_name: str = Form(...),
    description: Optional[str] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a personal document file (PDF, JPG, PNG, DOC, DOCX up to 10MB) via FastAPI."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found.")

    # Validate file extension
    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Allowed extensions: PDF, JPG, JPEG, PNG, DOC, DOCX."
        )

    # Save physical file
    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)

    file_bytes = await file.read()
    file_size = len(file_bytes)

    # 10 MB limit check
    if file_size > Config.MAX_CONTENT_LENGTH:
        raise HTTPException(status_code=413, detail="File size exceeds the 10 MB maximum limit.")

    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'bin'
    unique_prefix = uuid.uuid4().hex[:12]
    stored_filename = f"{unique_prefix}_{file.filename}"
    file_path = os.path.join(upload_folder, stored_filename)

    with open(file_path, "wb") as f:
        f.write(file_bytes)

    new_doc = Document(
        user_id=user.id,
        category_id=category.id,
        document_name=document_name,
        description=description,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file_ext.upper(),
        file_size=file_size
    )

    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return DocumentResponseSchema(
        id=new_doc.id,
        user_id=new_doc.user_id,
        category_id=new_doc.category_id,
        category_name=category.name,
        document_name=new_doc.document_name,
        description=new_doc.description,
        original_filename=new_doc.original_filename,
        file_type=new_doc.file_type,
        file_size=new_doc.file_size,
        formatted_file_size=new_doc.formatted_file_size,
        upload_date=new_doc.upload_date
    )

@app.get("/api/documents/{doc_id}", response_model=DocumentResponseSchema, tags=["Documents"])
def get_document_by_id(doc_id: int, db: Session = Depends(get_db)):
    """Fetch metadata of a single document by its ID."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentResponseSchema(
        id=doc.id,
        user_id=doc.user_id,
        category_id=doc.category_id,
        category_name=doc.category.name if doc.category else None,
        document_name=doc.document_name,
        description=doc.description,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        formatted_file_size=doc.formatted_file_size,
        upload_date=doc.upload_date
    )

@app.get("/api/documents/{doc_id}/download", tags=["Documents"])
def download_document_file(doc_id: int, db: Session = Depends(get_db)):
    """Stream and download the physical document file."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not os.path.exists(doc.file_path):
        raise HTTPException(status_code=404, detail="Physical file missing from server storage.")

    return FileResponse(
        path=doc.file_path,
        filename=doc.original_filename,
        media_type="application/octet-stream"
    )

@app.put("/api/documents/{doc_id}", response_model=DocumentResponseSchema, tags=["Documents"])
def update_document(doc_id: int, payload: DocumentUpdateSchema, db: Session = Depends(get_db)):
    """Update document name, category, or description."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if payload.document_name is not None:
        doc.document_name = payload.document_name
    if payload.category_id is not None:
        doc.category_id = payload.category_id
    if payload.description is not None:
        doc.description = payload.description

    doc.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(doc)

    return DocumentResponseSchema(
        id=doc.id,
        user_id=doc.user_id,
        category_id=doc.category_id,
        category_name=doc.category.name if doc.category else None,
        document_name=doc.document_name,
        description=doc.description,
        original_filename=doc.original_filename,
        file_type=doc.file_type,
        file_size=doc.file_size,
        formatted_file_size=doc.formatted_file_size,
        upload_date=doc.upload_date
    )

@app.delete("/api/documents/{doc_id}", tags=["Documents"])
def delete_document(doc_id: int, db: Session = Depends(get_db)):
    """Permanently delete a document record and its physical storage file."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    # Delete physical file from disk
    delete_document_file(doc.file_path)

    # Delete database record
    db.delete(doc)
    db.commit()

    return {"status": "success", "message": f"Document '{doc.document_name}' deleted successfully."}

# -------------------------------------------------------------
# System Statistics Endpoint
# -------------------------------------------------------------

@app.get("/api/stats", response_model=DashboardStatsSchema, tags=["Analytics"])
def get_system_statistics(db: Session = Depends(get_db)):
    """Get overall platform metrics, user counts, and category statistics."""
    total_users = db.query(User).filter(User.role != 'admin').count()
    total_documents = db.query(Document).count()
    total_categories = db.query(Category).count()

    categories = db.query(Category).all()
    cat_breakdown = []
    for cat in categories:
        count = db.query(Document).filter(Document.category_id == cat.id).count()
        cat_breakdown.append({"category": cat.name, "count": count})

    # Group by file type
    docs = db.query(Document).all()
    type_counts = {}
    for d in docs:
        type_counts[d.file_type] = type_counts.get(d.file_type, 0) + 1
    type_breakdown = [{"file_type": k, "count": v} for k, v in type_counts.items()]

    return DashboardStatsSchema(
        total_users=total_users,
        total_documents=total_documents,
        total_categories=total_categories,
        categories_breakdown=cat_breakdown,
        file_types_breakdown=type_breakdown
    )

if __name__ == "__main__":
    import uvicorn
    # Run FastAPI server on port 8000
    uvicorn.run("fastapi_app:app", host="0.0.0.0", port=8000, reload=True)
