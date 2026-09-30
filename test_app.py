import io
import unittest
from app import create_app
from models import db, User, Category, Document

class TestPersonalDocumentOrganizer(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def test_01_public_redirect(self):
        """Test root redirect to login for unauthenticated visitor."""
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.headers['Location'])

    def test_02_login_pages(self):
        """Test authentication pages load successfully."""
        resp = self.client.get('/login')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Sign In', resp.data)

        resp = self.client.get('/register')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Create Account', resp.data)

        resp = self.client.get('/forgot-password')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Reset Password', resp.data)

    def test_03_user_registration_and_dashboard(self):
        """Test dynamic user registration, login, and dashboard access."""
        # 1. Register new user
        reg_resp = self.client.post('/register', data={
            'full_name': 'Test Student',
            'email': 'student@example.com',
            'phone': '+1234567890',
            'password': 'Password@123',
            'confirm_password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(reg_resp.status_code, 200)

        # 2. Login
        login_resp = self.client.post('/login', data={
            'email': 'student@example.com',
            'password': 'Password@123'
        }, follow_redirects=True)
        self.assertEqual(login_resp.status_code, 200)
        self.assertIn(b'User Dashboard', login_resp.data)
        self.assertIn(b'Test Student', login_resp.data)

    def test_04_user_upload_view_and_search(self):
        """Test user document upload, view, download, and search."""
        # Log in as test student
        self.client.post('/login', data={'email': 'student@example.com', 'password': 'Password@123'})

        # Get education category id
        with self.app.app_context():
            cat = Category.query.first()
            cat_id = cat.id if cat else 1

        # Upload a test document
        upload_resp = self.client.post('/upload', data={
            'document_name': 'Semester Marksheet Test',
            'category_id': str(cat_id),
            'description': 'Final year examination grades',
            'document_file': (io.BytesIO(b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF'), 'marksheet_test.pdf')
        }, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(upload_resp.status_code, 200)
        self.assertIn(b'Document uploaded successfully.', upload_resp.data)

        # View document
        with self.app.app_context():
            user = User.query.filter_by(email='student@example.com').first()
            doc = Document.query.filter_by(user_id=user.id).first()
            self.assertIsNotNone(doc)
            doc_id = doc.id

        view_resp = self.client.get(f'/document/{doc_id}/view')
        self.assertEqual(view_resp.status_code, 200)
        self.assertIn(b'Semester Marksheet Test', view_resp.data)

        # Download document
        dl_resp = self.client.get(f'/document/{doc_id}/download')
        self.assertEqual(dl_resp.status_code, 200)
        self.assertIn('attachment', dl_resp.headers.get('Content-Disposition', ''))

        # Search documents
        search_resp = self.client.get('/search?q=Marksheet')
        self.assertEqual(search_resp.status_code, 200)
        self.assertIn(b'Semester Marksheet Test', search_resp.data)

        # Categories page
        cat_resp = self.client.get('/categories')
        self.assertEqual(cat_resp.status_code, 200)

        # Profile page
        profile_resp = self.client.get('/profile')
        self.assertEqual(profile_resp.status_code, 200)
        self.assertIn(b'Test Student', profile_resp.data)

    def test_05_admin_authorization_protection(self):
        """Test that regular users are blocked from admin routes (HTTP 403)."""
        self.client.post('/login', data={'email': 'student@example.com', 'password': 'Password@123'})
        resp = self.client.get('/admin/dashboard')
        self.assertEqual(resp.status_code, 403)

    def test_06_admin_login_and_features(self):
        """Test admin login and administration endpoints."""
        self.client.get('/logout')
        resp = self.client.post('/login', data={
            'email': 'admin@gmail.com',
            'password': 'Admin@123'
        }, follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Admin Dashboard', resp.data)

        # Users management
        resp = self.client.get('/admin/users')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Registered Users', resp.data)

        # Documents management
        resp = self.client.get('/admin/documents')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'All Documents', resp.data)

        # Categories management
        resp = self.client.get('/admin/categories')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'Document Categories', resp.data)

        # Reports
        resp = self.client.get('/admin/reports')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'System Audit & Usage Report', resp.data)

        # Export CSV
        resp = self.client.get('/admin/reports/export-csv')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers.get('Content-Type'), 'text/csv; charset=utf-8')
        self.assertIn(b'Document ID,Document Name', resp.data)

if __name__ == '__main__':
    unittest.main()
