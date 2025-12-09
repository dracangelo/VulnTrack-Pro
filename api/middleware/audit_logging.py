"""
Audit logging system for tracking user actions.
Logs who did what and when for security and compliance.
"""
from datetime import datetime
from flask import request, g, session
from api.extensions import db
import json


class AuditLog(db.Model):
    """
    Audit log model for tracking user actions.
    """
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    
    # User information
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    username = db.Column(db.String(100), nullable=True)
    ip_address = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    
    # Action information
    action = db.Column(db.String(100), nullable=False, index=True)  # e.g., 'CREATE_TARGET', 'DELETE_SCAN'
    resource_type = db.Column(db.String(50), nullable=False)  # e.g., 'target', 'scan', 'user'
    resource_id = db.Column(db.Integer, nullable=True)
    
    # Request information
    method = db.Column(db.String(10), nullable=False)  # GET, POST, PUT, DELETE
    endpoint = db.Column(db.String(200), nullable=False)
    status_code = db.Column(db.Integer, nullable=True)
    
    # Additional details
    details = db.Column(db.Text, nullable=True)  # JSON string with additional info
    user_agent = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<AuditLog {self.id}: {self.username} - {self.action} on {self.resource_type}>'
    
    def to_dict(self):
        """Convert audit log to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'username': self.username,
            'ip_address': self.ip_address,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'method': self.method,
            'endpoint': self.endpoint,
            'status_code': self.status_code,
            'details': json.loads(self.details) if self.details else None,
            'user_agent': self.user_agent
        }


def log_action(action, resource_type, resource_id=None, details=None, status_code=None):
    """
    Log a user action to the audit log.
    
    Args:
        action: Action performed (e.g., 'CREATE', 'UPDATE', 'DELETE', 'VIEW')
        resource_type: Type of resource (e.g., 'target', 'scan', 'user')
        resource_id: ID of the resource (optional)
        details: Additional details as dictionary (optional)
        status_code: HTTP status code (optional)
    """
    try:
        # Get user information
        user_id = session.get('user_id')
        username = session.get('username', 'anonymous')
        
        # Try to get from JWT if session doesn't have it
        if not user_id:
            try:
                from flask_jwt_extended import get_jwt_identity
                jwt_user = get_jwt_identity()
                if jwt_user:
                    username = jwt_user
            except:
                pass
        
        # Create audit log entry
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            ip_address=request.remote_addr or 'unknown',
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            method=request.method,
            endpoint=request.path,
            status_code=status_code,
            details=json.dumps(details) if details else None,
            user_agent=request.headers.get('User-Agent', '')[:500]
        )
        
        db.session.add(audit_log)
        db.session.commit()
        
    except Exception as e:
        # Don't let audit logging failures break the application
        import logging
        logging.error(f"Failed to create audit log: {str(e)}")
        db.session.rollback()


def audit_log_decorator(action, resource_type):
    """
    Decorator to automatically log actions.
    
    Usage:
        @audit_log_decorator('CREATE', 'target')
        def create_target():
            # ... create target logic
            return jsonify({'id': target.id}), 201
    """
    from functools import wraps
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Execute the function
            response = f(*args, **kwargs)
            
            # Extract resource_id from response if possible
            resource_id = None
            status_code = 200
            
            if isinstance(response, tuple):
                data, status_code = response[0], response[1]
                if hasattr(data, 'json'):
                    json_data = data.json
                    resource_id = json_data.get('id')
            
            # Log the action
            log_action(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status_code=status_code
            )
            
            return response
        
        return decorated_function
    return decorator


def init_audit_logging(app):
    """
    Initialize audit logging middleware.
    
    Args:
        app: Flask application instance
    """
    # Log all state-changing requests
    @app.after_request
    def log_request(response):
        # Only log state-changing methods and important GET requests
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            # Determine action from method
            action_map = {
                'POST': 'CREATE',
                'PUT': 'UPDATE',
                'PATCH': 'UPDATE',
                'DELETE': 'DELETE'
            }
            action = action_map.get(request.method, 'ACTION')
            
            # Extract resource type from path
            path_parts = request.path.split('/')
            resource_type = path_parts[2] if len(path_parts) > 2 else 'unknown'
            
            # Extract resource ID if present
            resource_id = None
            try:
                # Try to get ID from URL (e.g., /api/targets/123)
                if len(path_parts) > 3 and path_parts[3].isdigit():
                    resource_id = int(path_parts[3])
            except:
                pass
            
            # Log the action
            log_action(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                status_code=response.status_code
            )
        
        return response
    
    # Log authentication events
    @app.before_request
    def log_auth_events():
        # Log login attempts
        if request.path.endswith('/login') and request.method == 'POST':
            g.log_auth = True
    
    app.logger.info("Audit logging middleware initialized")


def get_audit_logs(user_id=None, resource_type=None, action=None, limit=100, offset=0):
    """
    Retrieve audit logs with optional filters.
    
    Args:
        user_id: Filter by user ID
        resource_type: Filter by resource type
        action: Filter by action
        limit: Maximum number of logs to return
        offset: Offset for pagination
        
    Returns:
        list: List of audit log dictionaries
    """
    query = AuditLog.query
    
    if user_id:
        query = query.filter_by(user_id=user_id)
    
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    
    if action:
        query = query.filter_by(action=action)
    
    # Order by timestamp descending (most recent first)
    query = query.order_by(AuditLog.timestamp.desc())
    
    # Apply pagination
    logs = query.limit(limit).offset(offset).all()
    
    return [log.to_dict() for log in logs]


def get_user_activity(user_id, days=30):
    """
    Get activity summary for a user.
    
    Args:
        user_id: User ID
        days: Number of days to look back
        
    Returns:
        dict: Activity summary
    """
    from datetime import timedelta
    
    since = datetime.utcnow() - timedelta(days=days)
    
    logs = AuditLog.query.filter(
        AuditLog.user_id == user_id,
        AuditLog.timestamp >= since
    ).all()
    
    # Count actions by type
    action_counts = {}
    for log in logs:
        action_counts[log.action] = action_counts.get(log.action, 0) + 1
    
    return {
        'user_id': user_id,
        'period_days': days,
        'total_actions': len(logs),
        'action_counts': action_counts,
        'last_activity': logs[0].timestamp.isoformat() if logs else None
    }
