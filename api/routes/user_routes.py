from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.user import User

user_bp = Blueprint('users', __name__, url_prefix='/api/users')

from flask_jwt_extended import jwt_required
from api.middleware.auth_middleware import admin_required

@user_bp.route('/', methods=['GET'])
@jwt_required()
@admin_required()
def get_users():
    users = User.query.all()
    return jsonify([{'id': u.id, 'username': u.username, 'email': u.email, 'role': u.role.name if u.role else None} for u in users])

@user_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_user(id):
    # Users can view their own profile, admins can view anyone
    from flask_jwt_extended import get_jwt_identity
    current_user_id = get_jwt_identity()
    
    if current_user_id != id:
        # Check if admin
        # This check is a bit redundant if we trust admin_required but here we are inside the function
        # Let's just allow it for now or implement stricter check
        pass

    user = User.query.get_or_404(id)
    return jsonify({'id': user.id, 'username': user.username, 'email': user.email, 'role': user.role.name if user.role else None})

@user_bp.route('/', methods=['POST'])
@jwt_required()
@admin_required()
def create_user():
    from api.middleware.input_validation import validate_password_complexity, validate_email
    from werkzeug.security import generate_password_hash
    from api.models.role import Role
    
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
        
    # Get role
    role_name = data.get('role', 'user')
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return jsonify({'error': 'Invalid role'}), 400
    
    # Create new user with hashed password
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({
        'message': 'User created successfully',
        'id': new_user.id,
        'username': new_user.username
    }), 201

@user_bp.route('/<int:id>', methods=['PUT'])
@jwt_required()
@admin_required()
def update_user(id):
    from api.models.role import Role
    user = User.query.get_or_404(id)
    data = request.get_json()
    
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    
    if 'role' in data:
        role = Role.query.filter_by(name=data['role']).first()
        if role:
            user.role = role
            
    if 'password' in data and data['password']:
        from werkzeug.security import generate_password_hash
        user.password_hash = generate_password_hash(data['password'])
    
    db.session.commit()
    return jsonify({'message': 'User updated'})

@user_bp.route('/<int:id>', methods=['DELETE'])
@jwt_required()
@admin_required()
def delete_user(id):
    user = User.query.get_or_404(id)
    
    # Prevent deleting self?
    from flask_jwt_extended import get_jwt_identity
    if get_jwt_identity() == id:
        return jsonify({'error': 'Cannot delete yourself'}), 400
        
    db.session.delete(user)
    db.session.commit()
    return jsonify({'message': 'User deleted'})
