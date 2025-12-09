"""
CSRF Protection middleware for Flask application.
Implements Cross-Site Request Forgery protection using Flask-WTF.
"""
from flask_wtf.csrf import CSRFProtect
from flask import jsonify

csrf = CSRFProtect()


def init_csrf_protection(app):
    """
    Initialize CSRF protection.
    
    Args:
        app: Flask application instance
    """
    # Initialize CSRF protection
    csrf.init_app(app)
    
    # Configure CSRF settings
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = None  # No time limit for tokens
    app.config['WTF_CSRF_SSL_STRICT'] = False  # Set to True in production with HTTPS
    app.config['WTF_CSRF_CHECK_DEFAULT'] = True
    
    # Exempt certain routes from CSRF protection (e.g., API endpoints with token auth)
    csrf.exempt('api.auth.login')  # Login endpoint
    csrf.exempt('api.auth.register')  # Register endpoint
    csrf.exempt('api.health')  # Health check
    
    # Custom error handler for CSRF failures
    @csrf.error_handler
    def csrf_error(reason):
        return jsonify({
            'error': 'CSRF validation failed',
            'reason': reason
        }), 400
    
    app.logger.info("CSRF protection initialized")
    
    return csrf


def get_csrf_token():
    """
    Generate and return a CSRF token.
    Can be called from routes to get a token for the frontend.
    """
    from flask_wtf.csrf import generate_csrf
    return generate_csrf()
