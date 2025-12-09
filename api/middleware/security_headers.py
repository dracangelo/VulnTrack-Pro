"""
Security headers middleware for Flask application.
Adds security headers to all responses to protect against common web vulnerabilities.
"""
from flask import make_response


def add_security_headers(response):
    """
    Add security headers to response.
    
    Headers added:
    - Content-Security-Policy: Prevents XSS attacks
    - X-Content-Type-Options: Prevents MIME sniffing
    - X-Frame-Options: Prevents clickjacking
    - X-XSS-Protection: Enables browser XSS protection
    - Strict-Transport-Security: Forces HTTPS
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    """
    # Content Security Policy - Prevents XSS and injection attacks
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' cdnjs.cloudflare.com fonts.googleapis.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' cdnjs.cloudflare.com fonts.gstatic.com; "
        "connect-src 'self' ws: wss:; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )
    response.headers['Content-Security-Policy'] = csp
    
    # Prevent MIME type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    
    # Prevent clickjacking attacks
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Enable browser XSS protection (legacy, but still useful)
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # Force HTTPS (only in production)
    # Uncomment in production with HTTPS enabled
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    
    # Control referrer information
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    
    # Control browser features
    response.headers['Permissions-Policy'] = (
        'geolocation=(), '
        'microphone=(), '
        'camera=(), '
        'payment=(), '
        'usb=(), '
        'magnetometer=(), '
        'gyroscope=(), '
        'accelerometer=()'
    )
    
    return response


def init_security_headers(app):
    """
    Initialize security headers middleware.
    
    Args:
        app: Flask application instance
    """
    @app.after_request
    def apply_security_headers(response):
        return add_security_headers(response)
    
    app.logger.info("Security headers middleware initialized")
