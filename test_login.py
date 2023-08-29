import unittest
import json
from app import app

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.headers = {'Content-Type': 'application/json'}

    def test_login_success(self):
        data = {
            "username": "company_one",
            "password": "password456"
        }
        response = self.app.post('/login', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", data)
        self.assertEqual(data['message'], "Login successful")

    def test_login_invalid_credentials(self):
        data = {
            "username": "nonexistentuser",
            "password": "wrongpassword"
        }
        response = self.app.post('/login', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['message'], "Invalid credentials")

if __name__ == '__main__':
    unittest.main()