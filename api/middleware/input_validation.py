"""
Input validation middleware and utilities.
Provides validation functions for common input types to prevent injection attacks.
"""
import re
from functools import wraps
from flask import request, jsonify
import bleach


def sanitize_html(text):
    """
    Sanitize HTML input to prevent XSS attacks.
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        Sanitized text with dangerous HTML removed
    """
    if not text:
        return text
    
    # Allow only safe tags
    allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li', 'code', 'pre']
    allowed_attributes = {'a': ['href', 'title']}
    
    return bleach.clean(
        text,
        tags=allowed_tags,
        attributes=allowed_attributes,
        strip=True
    )


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_complexity(password):
    """
    Validate password complexity requirements.
    
    Requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: Password to validate
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    
    return True, None


def validate_ip_address(ip):
    """
    Validate IP address format (IPv4 or IPv6).
    
    Args:
        ip: IP address to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not ip:
        return False
    
    # IPv4 pattern
    ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if re.match(ipv4_pattern, ip):
        parts = ip.split('.')
        return all(0 <= int(part) <= 255 for part in parts)
    
    # IPv6 pattern (simplified)
    ipv6_pattern = r'^([0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    return bool(re.match(ipv6_pattern, ip))


def validate_json_input(required_fields=None, optional_fields=None):
    """
    Decorator to validate JSON input for API endpoints.
    
    Args:
        required_fields: List of required field names
        optional_fields: List of optional field names
        
    Returns:
        Decorated function
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check if request has JSON data
            if not request.is_json:
                return jsonify({'error': 'Request must be JSON'}), 400
            
            data = request.get_json()
            
            # Validate required fields
            if required_fields:
                missing_fields = [field for field in required_fields if field not in data]
                if missing_fields:
                    return jsonify({
                        'error': 'Missing required fields',
                        'missing_fields': missing_fields
                    }), 400
            
            # Check for unexpected fields (optional, for strict validation)
            if required_fields or optional_fields:
                allowed_fields = set(required_fields or []) | set(optional_fields or [])
                unexpected_fields = [field for field in data.keys() if field not in allowed_fields]
                if unexpected_fields:
                    return jsonify({
                        'warning': 'Unexpected fields will be ignored',
                        'unexpected_fields': unexpected_fields
                    }), 400
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def sanitize_input_data(data):
    """
    Recursively sanitize input data dictionary.
    
    Args:
        data: Dictionary of input data
        
    Returns:
        Sanitized dictionary
    """
    if isinstance(data, dict):
        return {key: sanitize_input_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [sanitize_input_data(item) for item in data]
    elif isinstance(data, str):
        # Remove any potential SQL injection characters
        # This is a basic sanitization, use parameterized queries for SQL
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE']
        sanitized = data
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()
    else:
        return data


def init_input_validation(app):
    """
    Initialize input validation middleware.
    
    Args:
        app: Flask application instance
    """
    # Add before_request handler to log and validate requests
    @app.before_request
    def validate_request():
        # Log request for security auditing
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            app.logger.info(f"{request.method} {request.path} from {request.remote_addr}")
        
        # Add custom validation logic here if needed
        pass
    
    app.logger.info("Input validation middleware initialized")
