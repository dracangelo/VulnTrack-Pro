"""
Session configuration middleware.
Configures secure session management with timeout and security settings.
"""
from datetime import timedelta
from flask import session, request, jsonify
import secrets


def init_session_config(app):
    """
    Initialize secure session configuration.
    
    Args:
        app: Flask application instance
    """
    # Generate a secure secret key if not set
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = secrets.token_hex(32)
        app.logger.warning("Generated random SECRET_KEY. Set SECRET_KEY in environment for production!")
    
    # Session configuration
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    app.config['SESSION_COOKIE_NAME'] = 'vulntrack_session'
    
    # Session timeout (30 minutes of inactivity)
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
    
    # Session refresh on activity
    @app.before_request
    def make_session_permanent():
        """Make session permanent and refresh on each request."""
        session.permanent = True
        
        # Check for session timeout
        if 'last_activity' in session:
            from datetime import datetime
            last_activity = session['last_activity']
            
            # Convert to datetime if it's a string
            if isinstance(last_activity, str):
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            
            # Ensure both datetimes are timezone-naive for comparison
            now = datetime.utcnow()
            if hasattr(last_activity, 'tzinfo') and last_activity.tzinfo is not None:
                # Convert timezone-aware to naive UTC
                last_activity = last_activity.replace(tzinfo=None)
            
            # If more than 30 minutes since last activity, clear session
            if (now - last_activity).total_seconds() > 1800:  # 30 minutes
                session.clear()
                return jsonify({'error': 'Session expired. Please login again.'}), 401
        
        # Update last activity timestamp (timezone-naive)
        from datetime import datetime
        session['last_activity'] = datetime.utcnow()
    
    # Session cleanup on logout
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        """Clear session on logout."""
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200
    
    app.logger.info(f"Session configuration initialized (timeout: 30 minutes)")


def require_session(f):
    """
    Decorator to require active session for route access.
    
    Usage:
        @app.route('/protected')
        @require_session
        def protected_route():
            return 'Protected content'
    """
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    
    return decorated_function


def get_session_info():
    """
    Get current session information.
    
    Returns:
        dict: Session information
    """
    from datetime import datetime
    
    if 'user_id' not in session:
        return None
    
    last_activity = session.get('last_activity')
    if last_activity:
        # Convert to datetime if it's a string
        if isinstance(last_activity, str):
            last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
        
        # Ensure timezone-naive for comparison
        now = datetime.utcnow()
        if hasattr(last_activity, 'tzinfo') and last_activity.tzinfo is not None:
            last_activity = last_activity.replace(tzinfo=None)
        
        time_remaining = 1800 - (now - last_activity).total_seconds()
    else:
        time_remaining = 1800
    
    return {
        'user_id': session.get('user_id'),
        'username': session.get('username'),
        'last_activity': last_activity.isoformat() if last_activity and hasattr(last_activity, 'isoformat') else str(last_activity),
        'time_remaining_seconds': max(0, int(time_remaining)),
        'expires_in_minutes': max(0, int(time_remaining / 60))
    }
