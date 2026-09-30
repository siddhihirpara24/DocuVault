# DocuVault - Personal Document Organizer

A secure, beginner-friendly, and professional web application to store, organize, search, preview, download, and manage personal documents (such as marksheets, degrees, ID proofs, and certificates) from one place.

Developed as an **MCA College Project** and portfolio project using **Python, Flask, FastAPI, MySQL / SQLite, and Bootstrap 5**.

---

## Key Features

### User Panel
* **User Registration & Login:** Secure authentication with password hashing.
* **Document Upload:** Upload documents (PDF, JPG, PNG, DOC, DOCX up to 10 MB) with category tagging.
* **In-Browser Preview:** View PDF files and images directly inside the browser.
* **Search & Filters:** Search files by name, description, category, or file format.
* **Edit & Replace:** Update document details or replace the attached file anytime.
* **Download & Delete:** Download original files securely or delete them with confirmation.
* **Categories:** View files organized by Education, Identity, Career, Financial, etc.
* **Strict Security:** Users can **only** see and manage their own documents.

### Admin Panel
* **Admin Dashboard:** Overview of total users, uploaded documents, and visual Chart.js analytics.
* **Manage Users:** View registered users, view user documents, and activate/deactivate accounts.
* **Manage Documents:** Browse and audit documents uploaded across the entire system.
* **Manage Categories:** Add, edit, or delete categories.
* **Reports & Export:** View platform statistics and export metadata to **CSV**.

### FastAPI & Swagger UI
* High-performance asynchronous REST API powered by **FastAPI**.
* Automatic interactive **Swagger UI** documentation at `http://127.0.0.1:8000/docs`.

---

## Technology Stack

* **Backend:** Python 3, Flask, FastAPI, SQLAlchemy ORM, Uvicorn
* **Frontend:** HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js
* **Database:** MySQL 8.0+ *(with automatic fallback to SQLite)*
* **Authentication:** Flask-Login, Werkzeug Security (Password Hashing)
* **Testing:** Python `unittest`

---

## Project Structure

```text
Document_management/
├── app.py                  # Main Flask Web Application
├── fastapi_app.py          # FastAPI REST API & Swagger UI
├── config.py               # Configuration & Database Settings
├── init_db.py              # Database Initialization Script
├── test_app.py             # Flask Unit Tests
├── test_fastapi.py         # FastAPI Unit Tests
├── requirements.txt        # Python Dependencies
├── .env                    # Environment Variables
├── database/
│   ├── schema.sql          # MySQL Database Schema
│   └── document_organizer.db # SQLite Database (Fallback)
├── models/                 # Database Models (User, Document, Category)
├── routes/                 # Flask Blueprints (auth, user, admin)
├── templates/              # HTML Templates (Bootstrap 5)
├── static/                 # CSS and JavaScript Files
└── uploads/                # Physical File Storage Folder
```

---

## How to Run the Project

### 1. Install Dependencies
Open terminal or PowerShell in the project directory:
```powershell
python -m pip install -r requirements.txt
```

### 2. (First-Time Only) Initialize Database
Run the setup script to create database tables, default categories, and the admin account:
```powershell
python init_db.py
```

### 3. Run the Web Application (Flask)
```powershell
python app.py
```
Open your browser and navigate to:  
**http://127.0.0.1:5000**

---

### 4. (Optional) Run the FastAPI REST Service & Swagger UI
To run the companion FastAPI REST API with interactive Swagger documentation:
```powershell
python fastapi_app.py
```
Open your browser and navigate to:  
**http://127.0.0.1:8000/docs**

---

## Default Administrator Login

* **Email:** `admin@gmail.com`
* **Password:** `Admin@123`

*(New users can create their own accounts using the **Register** page on the web interface).*

---

## Running Automated Tests

To test the Flask web application:
```powershell
python test_app.py
```

To test the FastAPI endpoints:
```powershell
python test_fastapi.py
```

---

## License
This project is developed for educational and academic submission purposes (MCA Project).
