import unittest
import json
from app import app

class TestCheckBalance(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.headers = {'Content-Type': 'application/json'}

    