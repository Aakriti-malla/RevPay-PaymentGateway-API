import unittest
from app import app  # Assuming your Flask app is named 'app'

class RegistrationTestCase(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_registration_successful(self):
        data = {
            "company_name": "Test Company",
            "username": "testuser",
            "password": "testpassword"
        }
        response = self.app.post('/register', json=data)
        data = response.get_json()

        self.assertEqual(response.status_code, 201)
        self.assertEqual(data['message'], 'Registration successful')

    def test_registration_missing_fields(self):
        data = {
            "company_name": "Test Company"
        }
        response = self.app.post('/register', json=data)
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Company name, username, and password are required')

    def test_registration_existing_username(self):
        data = {
            "company_name": "Test Company",
            "username": "testuser",
            "password": "testpassword"
        }
        
        response = self.app.post('/register', json=data)
        data = response.get_json()

        self.assertEqual(response.status_code, 409)
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'Username already exists')

if __name__ == '__main__':
    unittest.main()
