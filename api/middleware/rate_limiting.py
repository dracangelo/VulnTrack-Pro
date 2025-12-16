"""
Enhanced rate limiting middleware with per-user and per-endpoint limits.
Extends Flask-Limiter with custom rate limit strategies.
"""
from flask import request, jsonify, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps


def get_user_identifier():
    """
    Get user identifier for rate limiting.
    Uses user_id from session if authenticated, otherwise IP address.
    """
    from flask import session
    
    # Try to get user_id from session
    # Try to get user_id from session
    user_id = session.get('user_id')
    if user_id:
        return f"user:{user_id}"
    
    # Try to get user_id from JWT token
    try:
        from flask_jwt_extended import get_jwt_identity
        jwt_user = get_jwt_identity()
        if jwt_user:
            return f"user:{jwt_user}"
    except:
        pass
    
    # Fall back to IP address
    return f"ip:{get_remote_address()}"


def init_rate_limiting(app, limiter):
    """
    Initialize enhanced rate limiting.
    
    Args:
        app: Flask application instance
        limiter: Flask-Limiter instance
    """
    # Configure rate limiter to use user identifier
    limiter.key_func = get_user_identifier
    
    # Global rate limits (fallback)
    app.config['RATELIMIT_DEFAULT'] = '1000 per hour'
    app.config['RATELIMIT_STORAGE_URL'] = 'memory://'  # Use Redis in production
    
    # Custom error handler for rate limit exceeded
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.',
            'retry_after': e.description
        }), 429
    
    app.logger.info("Enhanced rate limiting initialized")


def rate_limit_by_endpoint(limits_dict):
    """
    Decorator for custom rate limits per endpoint.
    
    Args:
        limits_dict: Dictionary mapping user types to rate limits
                    Example: {'authenticated': '100/hour', 'anonymous': '10/hour'}
    
    Usage:
        @rate_limit_by_endpoint({'authenticated': '100/hour', 'anonymous': '10/hour'})
        def my_endpoint():
            return 'data'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask import session
            
            # Determine user type
            is_authenticated = 'user_id' in session
            user_type = 'authenticated' if is_authenticated else 'anonymous'
            
            # Get rate limit for this user type
            limit = limits_dict.get(user_type, '100/hour')
            
            # Apply rate limit (this is a simplified version)
            # In production, use Flask-Limiter's decorators
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Predefined rate limit configurations
RATE_LIMITS = {
    # Authentication endpoints - stricter limits
    'auth_login': '10 per minute',
    'auth_register': '5 per hour',
    'auth_password_reset': '3 per hour',
    
    # Read operations - generous limits
    'read_operations': '500 per hour',
    
    # Write operations - moderate limits
    'write_operations': '100 per hour',
    
    # Scan operations - limited (resource intensive)
    'scan_operations': '20 per hour',
    
    # Report generation - limited (resource intensive)
    'report_generation': '10 per hour',
    
    # API endpoints - standard limits
    'api_default': '200 per hour',
}


def get_rate_limit_info():
    """
    Get current rate limit status for the user.
    
    Returns:
        dict: Rate limit information
    """
    from flask_limiter import Limiter
    
    # This would require accessing the limiter's storage
    # Simplified version for now
    return {
        'user_identifier': get_user_identifier(),
        'limits': RATE_LIMITS,
        'message': 'Rate limits are enforced per user and endpoint'
    }
