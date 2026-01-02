import unittest
import sys
import os

# Add root to sys.path
sys.path.append(os.getcwd())

from app import create_app, db
from app.models import User
from app.utils.security import generate_salt, hash_password
import json

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Seed admin directly here
        salt = generate_salt()
        hashed_pw = hash_password('Fuzz_jitong_test', salt).hex()
        # Ensure we provide enough fields if models are strict, but basic should work
        admin = User(ID='admin_id', LOGINNAME='admin', PWD=hashed_pw, SALT=salt.hex(), NAME='Admin', STATUS='1')
        db.session.add(admin)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_login_success(self):
        response = self.client.post('/api/login', json={
            'username': 'admin',
            'password': 'Fuzz_jitong_test'
        })
        print(f"Login Success Status: {response.status_code}")
        print(f"Login Success Data: {response.data}")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['code'], 200)

    def test_login_fail(self):
        response = self.client.post('/api/login', json={
            'username': 'admin',
            'password': 'wrong_password'
        })
        print(f"Login Fail Status: {response.status_code}")
        print(f"Login Fail Data: {response.data}")
        self.assertEqual(response.status_code, 200) 
        data = json.loads(response.data)
        self.assertEqual(data['code'], 401)

    def test_access_control(self):
        # Access protected route without login
        response = self.client.post('/api/user/add', json={})
        # Access control in __init__.py returns (, 401)
        self.assertEqual(response.status_code, 401)

    def test_add_user_as_admin(self):
        # Login first
        with self.client:
            self.client.post('/api/login', json={
                'username': 'admin',
                'password': 'Fuzz_jitong_test'
            })
            # Add user
            response = self.client.post('/api/user/add', json={
                'username': 'newuser',
                'password': 'password123',
                'name': 'New User'
            })
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data['code'], 200)
            
            # Verify user exists
            user = User.query.filter_by(LOGINNAME='newuser').first()
            self.assertIsNotNone(user)
            self.assertEqual(user.NAME, 'New User')

if __name__ == '__main__':
    unittest.main()
