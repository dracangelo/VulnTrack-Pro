import pytest
from api.models.user import User
from api.models.role import Role
from api.extensions import db
import json

def test_registration_password_complexity(client, app):
    """Test password complexity during registration"""
    with app.app_context():
        # Ensure user doesn't exist
        user = User.query.filter_by(username='test_weak').first()
        if user:
            db.session.delete(user)
            db.session.commit()

    # 1. Test weak password (too short)
    response = client.post('/api/auth/register', json={
        'username': 'test_weak',
        'email': 'weak@example.com',
        'password': 'short'
    })
    assert response.status_code == 400
    assert 'at least 8 characters' in response.json['error']

    # 2. Test weak password (no uppercase)
    response = client.post('/api/auth/register', json={
        'username': 'test_weak',
        'email': 'weak@example.com',
        'password': 'password123!'
    })
    assert response.status_code == 400
    assert 'uppercase' in response.json['error']

    # 3. Test weak password (no special char)
    response = client.post('/api/auth/register', json={
        'username': 'test_weak',
        'email': 'weak@example.com',
        'password': 'Password123'
    })
    assert response.status_code == 400
    assert 'special character' in response.json['error']

    # 4. Test strong password
    response = client.post('/api/auth/register', json={
        'username': 'test_strong',
        'email': 'strong@example.com',
        'password': 'StrongP@ss1'
    })
    assert response.status_code == 201
    assert 'User registered successfully' in response.json['message']

def test_password_change_complexity(client, app, auth_headers):
    """Test password complexity during password change"""
    # 1. Login first (already done via auth_headers fixture usually, but let's be explicit if needed)
    # Assuming auth_headers provides a valid token for a test user
    
    # Create a test user if not exists (auth_headers usually relies on a fixture creating a user)
    # Let's assume 'testuser' exists with password 'testpassword' from conftest
    
    # We need to know the current password to change it. 
    # In standard conftest, it's often 'testpassword'.
    
    # 1. Try to change to weak password
    response = client.put('/api/auth/me', headers=auth_headers, json={
        'current_password': 'password123',
        'password': 'weak'
    })
    assert response.status_code == 400
    assert 'at least 8 characters' in response.json['error']

    # 2. Change to strong password
    response = client.put('/api/auth/me', headers=auth_headers, json={
        'current_password': 'password123',
        'password': 'NewStrongP@ss1'
    })
    assert response.status_code == 200
    assert 'Profile updated successfully' in response.json['message']
