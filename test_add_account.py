import unittest
import json
from app import app
from flask_jwt_extended import JWTManager, create_access_token

class TestAddAccountRoute(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.headers = {'Content-Type': 'application/json'}
        self.jwt_token = self.get_jwt_token()

    def get_jwt_token(self):
        jwt_token = create_access_token(identity=1)
        return jwt_token

    def test_add_account_success(self):
        data = {
            "bank_account_number": 2323232323,
            "ifsc_code": "ABCD1234",
            "transaction_type": "BOTH"
        }
        self.headers['Authorization'] = f"Bearer {self.jwt_token}"
        response = self.app.post('/add_account', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['message'], "Bank account created successfully")

    def test_add_account_duplicate_account_number(self):
        data = {
            "bank_account_number": 1234567890, 
            "ifsc_code": "EFGH5678",
            "transaction_type": "CREDIT"
        }
        response = self.app.post('/add_account', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 401)
        self.assertEqual(data['error'], "Bank account number already exists!")

    def test_invalid_transaction_type(self):
        data = {
            "bank_account_number": 9090909090, 
            "ifsc_code": "EFGH5678",
            "transaction_type": "INVALID"
        }

        response = self.app.post('/add_account', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 400)  
        self.assertEqual(data['error'], " Invalid 'transaction_type'. Allowed values are 'CREDIT', 'DEBIT' or 'BOTH' ")

    def test_missing_required_fields(self):
        data = {
            "bank_account_number": 9090989090, 
        }

        response = self.app.post('/add_account', headers=self.headers, data=json.dumps(data))
        data = response.get_json()

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['error'], "Bank account number and IFSC Code are required")


if __name__ == '__main__':
    unittest.main()
