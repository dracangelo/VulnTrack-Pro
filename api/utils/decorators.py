from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from api.models.user import User
from api.services.rbac_service import RBACService

def require_permission(resource, action):
    """Decorator to check if user has required permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get current user
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'error': 'User not found'}), 401
            
            if not RBACService.check_permission(user, resource, action):
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'You do not have permission to {action} {resource}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(*roles):
    """Decorator to check if user has required role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT token
            verify_jwt_in_request()
            
            # Get current user
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user or not user.role:
                return jsonify({'error': 'User not found'}), 401
            
            if user.role.name not in roles:
                return jsonify({
                    'error': 'Forbidden',
                    'message': f'Requires one of roles: {", ".join(roles)}'
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def optional_auth(f):
    """Decorator for optional authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
        except:
            pass  # No token is fine
        return f(*args, **kwargs)
    return decorated_function
