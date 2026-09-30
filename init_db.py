import os
import uuid
from datetime import datetime, timedelta
from app import create_app
from models import db, User, Category, Document

def init_and_seed():
    """Initialize database tables and seed required admin and sample demo data."""
    app = create_app()

    with app.app_context():
        print("Creating all database tables...")
        db.create_all()

        # 1. Seed Categories
        default_categories = [
            ("Education", "Academic transcripts, marksheets, degree certificates, and grade cards."),
            ("Identity", "Passport, National ID, Driving License, Voter ID, and citizen credentials."),
            ("Career", "Resumes, CVs, Offer letters, Experience certificates, and Payslips."),
            ("Financial", "Bank statements, Tax returns, Investment proofs, and Audit slips."),
            ("Bills", "Electricity, Internet bills, Rent receipts, and Utility vouchers."),
            ("Certificates", "Professional accreditations, Training certifications, and Workshop awards."),
            ("Medical", "Health insurance policies, Prescription notes, and Diagnostic reports."),
            ("Other", "Miscellaneous personal notes, Warranties, and General documentation.")
        ]

        categories_map = {}
        for cat_name, cat_desc in default_categories:
            cat = Category.query.filter_by(name=cat_name).first()
            if not cat:
                cat = Category(name=cat_name, description=cat_desc)
                db.session.add(cat)
                db.session.flush()
                print(f"  + Added category: {cat_name}")
            categories_map[cat_name] = cat

        # 2. Seed Admin User
        admin_email = "admin@gmail.com"
        admin_user = User.query.filter_by(email=admin_email).first()
        if not admin_user:
            admin_user = User(
                full_name="Administrator",
                email=admin_email,
                phone="+1 (555) 019-2834",
                role="admin",
                status="active"
            )
            admin_user.set_password("Admin@123")
            db.session.add(admin_user)
            print(f"  + Added Default Admin: {admin_email} / Admin@123")
        else:
            print(f"  * Admin user already exists: {admin_email}")

        db.session.commit()

        print("\nDatabase initialization complete!")
        print("--------------------------------------------------")
        print("Default Administrator Account:")
        print("  Email:    admin@gmail.com")
        print("  Password: Admin@123")
        print("--------------------------------------------------")
        print("New users can register via the Registration page.")

if __name__ == '__main__':
    init_and_seed()
