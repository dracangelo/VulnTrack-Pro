"""
Audit log routes for viewing and managing audit logs.
"""
from flask import Blueprint, jsonify, request
from api.middleware.audit_logging import get_audit_logs, get_user_activity, AuditLog
from api.extensions import db

audit_bp = Blueprint('audit', __name__, url_prefix='/api/audit')


@audit_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Get audit logs with optional filters.
    
    Query parameters:
        user_id: Filter by user ID
        resource_type: Filter by resource type (target, scan, user, etc.)
        action: Filter by action (CREATE, UPDATE, DELETE, etc.)
        limit: Maximum number of logs (default: 100, max: 1000)
        offset: Offset for pagination (default: 0)
    """
    # Get query parameters
    user_id = request.args.get('user_id', type=int)
    resource_type = request.args.get('resource_type')
    action = request.args.get('action')
    limit = min(request.args.get('limit', 100, type=int), 1000)
    offset = request.args.get('offset', 0, type=int)
    
    # Get logs
    logs = get_audit_logs(
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        limit=limit,
        offset=offset
    )
    
    # Get total count for pagination
    query = AuditLog.query
    if user_id:
        query = query.filter_by(user_id=user_id)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if action:
        query = query.filter_by(action=action)
    
    total = query.count()
    
    return jsonify({
        'logs': logs,
        'total': total,
        'limit': limit,
        'offset': offset,
        'has_more': (offset + limit) < total
    }), 200


@audit_bp.route('/user/<int:user_id>/activity', methods=['GET'])
def get_user_activity_summary(user_id):
    """
    Get activity summary for a specific user.
    
    Query parameters:
        days: Number of days to look back (default: 30)
    """
    days = request.args.get('days', 30, type=int)
    
    activity = get_user_activity(user_id, days=days)
    
    return jsonify(activity), 200


@audit_bp.route('/stats', methods=['GET'])
def get_audit_stats():
    """
    Get audit log statistics.
    
    Returns:
        - Total logs
        - Logs by action type
        - Logs by resource type
        - Most active users
    """
    from sqlalchemy import func
    
    # Total logs
    total_logs = AuditLog.query.count()
    
    # Logs by action
    action_stats = db.session.query(
        AuditLog.action,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.action).all()
    
    # Logs by resource type
    resource_stats = db.session.query(
        AuditLog.resource_type,
        func.count(AuditLog.id).label('count')
    ).group_by(AuditLog.resource_type).all()
    
    # Most active users (top 10)
    user_stats = db.session.query(
        AuditLog.username,
        func.count(AuditLog.id).label('count')
    ).filter(
        AuditLog.username != 'anonymous'
    ).group_by(AuditLog.username).order_by(
        func.count(AuditLog.id).desc()
    ).limit(10).all()
    
    return jsonify({
        'total_logs': total_logs,
        'by_action': {action: count for action, count in action_stats},
        'by_resource': {resource: count for resource, count in resource_stats},
        'top_users': [{'username': username, 'actions': count} for username, count in user_stats]
    }), 200


@audit_bp.route('/recent', methods=['GET'])
def get_recent_logs():
    """
    Get recent audit logs (last 24 hours).
    
    Query parameters:
        limit: Maximum number of logs (default: 50)
    """
    from datetime import datetime, timedelta
    
    limit = min(request.args.get('limit', 50, type=int), 500)
    since = datetime.utcnow() - timedelta(hours=24)
    
    logs = AuditLog.query.filter(
        AuditLog.timestamp >= since
    ).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'count': len(logs),
        'period': '24 hours'
    }), 200
