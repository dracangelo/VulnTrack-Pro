from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.user import User

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

@user_bp.route('/', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email} for u in users])

@user_bp.route('/<int:id>', methods=['GET'])
def get_user(id):
    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email})

@user_bp.route('/', methods=['POST'])
def create_user():
    from api.middleware.input_validation import validate_password_complexity, validate_email
    from werkzeug.security import generate_password_hash
    
    data = request.get_json()
    if not data or 'username' not in data or 'email' not in data or 'password' not in data:
        return jsonify({'error': 'Missing required fields: username, email, password'}), 400
    
    # Validate email format
    if not validate_email(data['email']):
        return jsonify({'error': 'Invalid email format'}), 400
    
    # Validate password complexity
    is_valid, error_message = validate_password_complexity(data['password'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
    
    # Check if username or email already exists
    existing_user = User.query.filter(
        (User.username == data['username']) | (User.email == data['email'])
    ).first()
    if existing_user:
        return jsonify({'error': 'Username or email already exists'}), 409
    
    # Create new user with hashed password
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password'])
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'id': new_user.id,
        'username': new_user.username
    }), 201

@user_bp.route('/<int:id>', methods=['PUT'])
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    
    db.session.commit()
    return jsonify({'message': 'User updated'})

@user_bp.route('/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})
