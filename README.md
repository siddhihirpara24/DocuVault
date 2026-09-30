# Personal Document Organizer (DocuVault)
**A Secure, Full-Featured Web Application for Managing, Organizing, and Auditing Personal Documents**

Developed as a professional **MCA Final Year / College Capstone Project** and resume portfolio project. Built with **Python 3**, **Flask**, **SQLAlchemy**, **MySQL**, **Bootstrap 5**, and **Chart.js**.

---

## 1. Project Overview & Problem Statement

### Problem Statement
In the digital age, individuals handle dozens of critical documents spanning academic degrees, identity credentials, employment contracts, tax filings, medical reports, and utility receipts. Most people store these documents haphazardly across email inboxes, local desktop folders, or messaging apps. This leads to:
- Difficulty retrieving documents quickly when needed for official applications.
- Risk of unauthorized file access.
- Inability to categorize, search, or audit documents systematically.

### Proposed Solution
**DocuVault (Personal Document Organizer)** is a centralized, role-based document management web platform designed to help users securely upload, categorize, preview, search, update, download, and delete their confidential personal documents. The system provides strict user-level data isolation, role-based administrator controls, dynamic analytics, and printable audit reports.

---

## 2. Key Features

### 🔐 1. Authentication & Security
- **Secure Registration:** Form validation (email format, password strength, confirmation matching, uniqueness check).
- **Password Hashing:** Implemented with Werkzeug's cryptographic hashing algorithms (`pbkdf2:sha256`).
- **Role-Based Access Control (RBAC):** Distinct permissions and routing for standard `user` and `admin` roles.
- **Strict Authorization Checks:** Users can **only** view, edit, download, or delete their own documents. Accessing another user's document ID returns an immediate **HTTP 403 Forbidden** error.
- **Password Reset Flow:** Secure token-based password reset system with expiry validation.
- **Account Status Guard:** Admins can deactivate abusive accounts; deactivated users cannot authenticate.

### 👤 2. User Panel
- **Dashboard:** Real-time statistics cards (Total, Education, Identity, Career, Other documents), recent uploads table, and quick action shortcuts.
- **Upload Document:**
  - Validates allowed extensions: `.pdf`, `.jpg`, `.jpeg`, `.png`, `.doc`, `.docx`.
  - Enforces a 10 MB maximum file size limit with both frontend and backend validation.
  - Automatically generates unique secure file identifiers to prevent filename collisions.
  - Physical files stored in `uploads/` directory; metadata indexed in MySQL.
- **My Documents:** Tabular management of all user files with sorting and category badges.
- **In-Browser Document Viewer:**
  - Embedded inline viewer for **PDF** files (`<iframe>`).
  - High-resolution viewer for **Image** files (`.jpg`, `.png`).
  - Clean metadata card and instant download button for unsupported formats (`.docx`).
- **File Replacement & Editing:** Edit document names, categories, and descriptions, or replace the attached physical file with automatic cleanup of obsolete files.
- **Safe Deletion:** Modal confirmation before permanent removal of physical file and database records.
- **Multifaceted Search:** Query by keyword (title/description), category, file format, and date ranges.
- **Category Explorer:** Card-based category browser with live document counters.
- **User Profile & Security:** Update personal profile info and change password with current password verification.

### 🛡️ 3. Admin Panel
- **Admin Dashboard:** High-level metrics (Total Users, Active Users, Total Documents, Documents Uploaded Today) plus interactive **Chart.js** data visualizations.
- **User Management:** View all registered users, inspection of documents per user, account activation/deactivation toggle, and account deletion with complete file cleanup. Self-deletion protection prevents admin lockout.
- **Document Audit:** Centralized listing of all system documents with multifaceted filters by user, category, file format, and date.
- **Category Management:** Add, edit, or delete categories with safeguards to reassign orphaned documents.
- **Reports & Analytics:**
  - Document distribution by category and file extension.
  - Monthly upload velocity over the last 6 months.
  - Printable system audit report (clean `@media print` layout).
  - **Export CSV:** One-click download of all document metadata in standard CSV format.

---

## 3. Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Bootstrap 5.3, Bootstrap Icons 1.11, Chart.js 4.4 |
| **Web Backend** | Python 3, Flask 3.x, Flask-Login, Flask-WTF, Werkzeug |
| **REST API Engine** | **FastAPI**, Uvicorn, Pydantic, OpenAPI / Swagger UI |
| **ORM & Database** | SQLAlchemy / Flask-SQLAlchemy, MySQL 8.0+ (PyMySQL) *(Automatic fallback to SQLite if MySQL is offline)* |
| **Storage** | Local disk storage (`uploads/`) with unique UUID hashing |

---

## 4. Database Architecture

The schema follows third normal form (3NF) principles with explicit foreign key constraints and cascade actions.

```
       +------------------+
       |      users       |
       +------------------+
       | id (PK)          |
       | full_name        |
       | email (Unique)   |
       | phone            |
       | password_hash    |
       | role             |
       | status           |
       | created_at       |
       +--------+---------+
                |
                | 1:N
                v
       +------------------+           +------------------+
       |    documents     |           |    categories    |
       +------------------+           +------------------+
       | id (PK)          |  N:1      | id (PK)          |
       | user_id (FK)     |---------->| name (Unique)    |
       | category_id (FK) |           | description      |
       | document_name    |           | created_at       |
       | original_filename|           +------------------+
       | stored_filename  |
       | file_path        |
       | file_type        |
       | file_size        |
       | upload_date      |
       +------------------+
                ^
                | 1:N
       +--------+-----------------+
       |  password_reset_tokens   |
       +--------------------------+
       | id (PK)                  |
       | user_id (FK)             |
       | token (Unique)           |
       | expires_at               |
       | created_at               |
       +--------------------------+
```

---

## 5. Project Folder Structure

```
Document_management/
├── app.py                     # Application factory and error handlers
├── config.py                  # Environment-aware configuration
├── requirements.txt           # Python package dependencies
├── init_db.py                 # Automated DB initialization and seeder script
├── test_app.py                # Complete unit and integration test suite
├── .env.example               # Template for environment variables
├── .env                       # Local environment variables
├── README.md                  # Comprehensive project documentation
├── database/
│   ├── schema.sql             # Pure MySQL DDL script
│   └── document_organizer.db  # SQLite database (when used)
├── models/
│   ├── __init__.py            # SQLAlchemy db instance
│   ├── user.py                # User model with authentication methods
│   ├── category.py            # Category classification model
│   ├── document.py            # Document metadata model
│   └── password_reset.py      # Token management model
├── routes/
│   ├── __init__.py            # Flask Blueprints registration
│   ├── auth.py                # Login, Register, Password Reset routes
│   ├── user.py                # User panel & document operations
│   └── admin.py               # Administrator controls & reports
├── static/
│   ├── css/
│   │   └── style.css          # Modern custom CSS styling
│   └── js/
│       └── script.js          # Client-side validation & UI interactions
├── templates/
│   ├── base.html              # Master layout
│   ├── errors/                # 403, 404, 500 error pages
│   ├── auth/                  # Authentication views
│   ├── user/                  # User dashboard and views
│   └── admin/                 # Administrator views
├── uploads/                   # Secure physical document storage folder
└── utils/
    ├── __init__.py
    ├── decorators.py          # @admin_required decorator
    └── helpers.py             # File saving, UUID generation, validation
```

---

## 6. Installation & Setup Instructions

### Prerequisites
- Python 3.10+ installed
- MySQL Server installed and running (Optional: SQLite runs automatically out-of-the-box)

### Step 1: Clone or Navigate to the Workspace
```powershell
cd "d:\Sem - 3\Project\Document_management"
```

### Step 2: Install Python Dependencies
```powershell
python -m pip install -r requirements.txt
```

### Step 3: Configure the Database in `.env`
Edit the `.env` file to match your local MySQL server credentials:
```ini
SECRET_KEY=personal-document-organizer-secret-key-2026
DATABASE_URL=mysql+pymysql://root:YOUR_PASSWORD@localhost:3306/document_organizer_db
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=10485760
FLASK_APP=app.py
FLASK_DEBUG=1
```
*(Note: If MySQL is not installed or the password is not yet configured, the system will automatically fall back to SQLite in `database/document_organizer.db`, so the app will run with zero errors!)*

### Step 4: Initialize and Seed the Database
Run the seed script to create all tables, default categories, and sample files:
```powershell
python init_db.py
```

### Step 5a: Start the Flask Web Application (Web Interface)
```powershell
python app.py
```
Open your web browser and navigate to:
```
http://127.0.0.1:5000
```

### Step 5b: (Optional) Start the FastAPI REST Service & Swagger UI
If you or your examiner want to test the pure **FastAPI REST API**:
```powershell
python fastapi_app.py
```
Open your browser to view the interactive OpenAPI Swagger documentation:
```
http://127.0.0.1:8000/docs
```
*(Alternative interactive documentation available at `http://127.0.0.1:8000/redoc`)*

---

## 7. Default Administrator Account

| Role | Email | Password | Access Capabilities |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@gmail.com` | `Admin@123` | Full Admin Panel, User Management, Reports, Global Audit |

*New standard users can register their own accounts directly via the **Register** page (`/register`).*

---

## 8. Running Automated Tests

Run the Flask automated test suite:
```powershell
python test_app.py
```

Run the FastAPI automated test suite:
```powershell
python test_fastapi.py
```

---

## 9. Viva / Interview Questions & Explanations

Here are key technical concepts an MCA student can explain during an exam, viva, or interview:

1. **Why store files on disk rather than as BLOBs in MySQL?**
   - Storing large binary files (PDFs, images) directly in SQL database tables causes table bloat, degrades database caching, slows down queries, and complicates backups.
   - The industry standard pattern is to store physical files on the server/cloud storage and store only lightweight metadata (file path, size, MIME type, owner ID) in relational database tables.

2. **How is unauthorized document access prevented?**
   - In [routes/user.py](file:///d:/Sem%20-%203/Project/Document_management/routes/user.py), every single document query performs an ownership check: `if document.user_id != current_user.id and not current_user.is_admin: abort(403)`. Changing an ID in the URL directly raises an HTTP 403 Forbidden error.

3. **How does filename collision prevention work?**
   - If two users upload `resume.pdf`, saving both under `resume.pdf` would overwrite data. We use `uuid.uuid4().hex[:12] + '_' + secure_filename(file.filename)` to guarantee a unique physical path while preserving the original name for downloads.

4. **Why Flask Blueprints?**
   - Flask Blueprints (`auth_bp`, `user_bp`, `admin_bp`) decouple routing logic into modular, maintainable packages, adhering to the Single Responsibility Principle.

---

## 10. Future Enhancements
- Cloud storage integration (AWS S3, Google Cloud Storage, or Azure Blob Storage).
- Two-Factor Authentication (TOTP via Google Authenticator).
- Optical Character Recognition (OCR) using Tesseract to search within scanned PDFs and images.
- Automatic document classification using Machine Learning models.
- Document expiration date notifications and email reminders.
