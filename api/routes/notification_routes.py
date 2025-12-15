from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.models.notification import Notification
from api.extensions import db

notification_bp = Blueprint('notifications', __name__, url_prefix='/api/notifications')

@notification_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get unread notifications for the current user."""
    current_user_id = get_jwt_identity()
    
    # Get unread notifications first, then read ones (limit total)
    notifications = Notification.query.filter_by(user_id=current_user_id)\
        .order_by(Notification.is_read.asc(), Notification.created_at.desc())\
        .limit(50).all()
        
    return jsonify([n.to_dict() for n in notifications])

@notification_bp.route('/<int:notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_as_read(notification_id):
    """Mark a notification as read."""
    current_user_id = get_jwt_identity()
    
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user_id: # Although JWT identity is string usually, ID is int. Check types if issues.
        # Assuming get_jwt_identity returns ID compatible with user_id
        # If get_jwt_identity returns string and user_id is int, cast it.
        # Usually flask-jwt-extended identity type depends on what was passed to create_access_token.
        # Let's assume it matches.
        if str(notification.user_id) != str(current_user_id):
             return jsonify({'error': 'Unauthorized'}), 403

    notification.is_read = True
    db.session.commit()
    
    return jsonify(notification.to_dict())

@notification_bp.route('/read-all', methods=['PUT'])
@jwt_required()
def mark_all_as_read():
    """Mark all notifications as read for current user."""
    current_user_id = get_jwt_identity()
    
    Notification.query.filter_by(user_id=current_user_id, is_read=False)\
        .update({Notification.is_read: True})
        
    db.session.commit()
    
    return jsonify({'message': 'All notifications marked as read'})
