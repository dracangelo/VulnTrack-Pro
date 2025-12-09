"""
Middleware package initialization.
Exports all middleware initialization functions.
"""
from api.middleware.security_headers import init_security_headers
from api.middleware.csrf_protection import init_csrf_protection
from api.middleware.input_validation import init_input_validation
from api.middleware.session_config import init_session_config
from api.middleware.rate_limiting import init_rate_limiting
from api.middleware.audit_logging import init_audit_logging

__all__ = [
    'init_security_headers',
    'init_csrf_protection',
    'init_input_validation',
    'init_session_config',
    'init_rate_limiting',
    'init_audit_logging',
]


def init_all_middleware(app):
    """
    Initialize all middleware components.
    
    Args:
        app: Flask application instance
    """
    from api.extensions import limiter
    
    init_security_headers(app)
    init_input_validation(app)
    init_session_config(app)
    init_rate_limiting(app, limiter)
    init_audit_logging(app)
    # CSRF protection requires flask-wtf, uncomment when installed
    # init_csrf_protection(app)
    
    app.logger.info("All middleware initialized successfully")
