from flask import Blueprint, jsonify, request
from api.models.activity_log import ActivityLog
from api.extensions import db

activity_bp = Blueprint('activity', __name__, url_prefix='/api/activity')

@activity_bp.route('/', methods=['GET'])
def get_activities():
    """Get all activity logs"""
    activities = ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(100).all()
    return jsonify([{
        'id': a.id,
        'action': a.action,
        'entity_type': a.entity_type,
        'entity_id': a.entity_id,
        'user_id': a.user_id,
        'timestamp': a.timestamp.isoformat() if a.timestamp else None,
        'details': a.details
    } for a in activities])
