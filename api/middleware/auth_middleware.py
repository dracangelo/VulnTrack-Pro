from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from api.models.user import User

def admin_required():
    """
    Decorator to ensure the current user has the 'admin' role.
    Must be used AFTER @jwt_required() or verify_jwt_in_request() must be called manually.
    """
    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.role or user.role.name != 'admin':
                return jsonify({'error': 'Admin privileges required'}), 403
                
            return fn(*args, **kwargs)
        return decorator
    return wrapper
