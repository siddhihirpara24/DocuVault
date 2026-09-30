import unittest
from fastapi.testclient import TestClient
from fastapi_app import app

class TestFastAPIApplication(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_01_health_check(self):
        """Test health endpoint."""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "healthy")

    def test_02_swagger_docs(self):
        """Test Swagger UI endpoint is accessible."""
        resp = self.client.get("/docs")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Swagger UI", resp.data if hasattr(resp, 'data') else resp.content)

    def test_03_openapi_json(self):
        """Test OpenAPI schema generation."""
        resp = self.client.get("/openapi.json")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("DocuVault", resp.json()["info"]["title"])

    def test_04_get_categories(self):
        """Test categories listing API."""
        resp = self.client.get("/api/categories")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(resp.json(), list)

    def test_05_admin_login_api(self):
        """Test authenticating admin via FastAPI."""
        resp = self.client.post("/api/auth/login", json={
            "email": "admin@gmail.com",
            "password": "Admin@123"
        })
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["status"], "success")

    def test_06_stats_api(self):
        """Test system statistics API."""
        resp = self.client.get("/api/stats")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_documents", data)
        self.assertIn("total_categories", data)

if __name__ == '__main__':
    unittest.main()
