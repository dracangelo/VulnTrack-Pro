from flask import Blueprint, jsonify, request
from api.services.collaboration_service import CollaborationService
from flask_jwt_extended import jwt_required, get_jwt_identity

collab_bp = Blueprint('collaboration', __name__, url_prefix='/api/collaboration')

@collab_bp.route('/comments', methods=['POST'])
@jwt_required()
def add_comment():
    """Add a comment to a resource."""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    text = data.get('text')
    resource_type = data.get('resource_type') # 'vulnerability' or 'ticket'
    resource_id = data.get('resource_id')
    parent_id = data.get('parent_id')
    
    if not text or not resource_type or not resource_id:
        return jsonify({'error': 'Missing required fields'}), 400
        
    try:
        comment = CollaborationService.add_comment(
            user_id=current_user_id,
            text=text,
            resource_type=resource_type,
            resource_id=resource_id,
            parent_id=parent_id
        )
        return jsonify(comment.to_dict()), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

@collab_bp.route('/comments/<resource_type>/<int:resource_id>', methods=['GET'])
@jwt_required()
def get_comments(resource_type, resource_id):
    """Get comments for a resource."""
    comments = CollaborationService.get_comments(resource_type, resource_id)
    
    # Helper to recursively serialize replies
    def serialize_comment(c):
        data = c.to_dict()
        data['replies'] = [serialize_comment(r) for r in c.replies]
        return data
        
    return jsonify([serialize_comment(c) for c in comments])

@collab_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity_feed():
    """Get user's activity feed."""
    current_user_id = get_jwt_identity()
    activities = CollaborationService.get_activity_feed(current_user_id)
    
    return jsonify([{
        'id': a.id,
        'user': a.user.username if a.user else 'System',
        'action': a.action,
        'target_type': a.target_type,
        'target_id': a.target_id,
        'details': a.details,
        'timestamp': a.timestamp.isoformat()
    } for a in activities])

@collab_bp.route('/activity/vulnerability/<int:vuln_id>', methods=['GET'])
@jwt_required()
def get_vulnerability_activity(vuln_id):
    """Get activity feed for a vulnerability."""
    activities = CollaborationService.get_vulnerability_activity(vuln_id)
    
    return jsonify([{
        'id': a.id,
        'user': a.user.username if a.user else 'System',
        'action': a.action,
        'details': a.details,
        'timestamp': a.timestamp.isoformat(),
        'type': 'activity' # Marker for frontend
    } for a in activities])
