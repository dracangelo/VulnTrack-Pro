from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api.extensions import db
from api.models.scan import Scan

scan_bp = Blueprint('scans', __name__, url_prefix='/api/scans')

@scan_bp.route('/', methods=['GET'])
@jwt_required()
def get_scans():
    from api.models.user import User
    from api.models.target import Target
    from api.models.team import Team
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    # Get user's team IDs
    team_ids = [t.id for t in user.teams]
    
    # Filter scans:
    # 1. Created by user
    # 2. OR Target belongs to one of user's teams
    from api.models.target import TargetGroup
    
    # Filter scans:
    # 1. Created by user
    # 2. OR Target belongs to one of user's teams
    scans = Scan.query.join(Target).outerjoin(TargetGroup).filter(
        (Scan.user_id == current_user_id) | 
        (TargetGroup.team_id.in_(team_ids))
    ).order_by(Scan.id.desc()).limit(20).all()
    
    return jsonify([{
        'id': s.id, 
        'target_id': s.target_id,
        'target_name': s.target.name if s.target else 'Unknown',
        'scan_type': s.scan_type, 
        'status': s.status,
        'created_at': s.started_at.isoformat() if s.started_at else None,
        'completed_at': s.completed_at.isoformat() if s.completed_at else None,
        'user_id': s.user_id
    } for s in scans])

@scan_bp.route('/<int:id>', methods=['GET'])
@jwt_required()
def get_scan(id):
    from api.models.user import User
    from api.models.target import Target
    from api.models.team import Team
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    scan = Scan.query.get_or_404(id)
    
    # Check permission
    is_owner = scan.user_id == int(current_user_id)
    is_team_member = False
    if scan.target and scan.target.group and scan.target.group.team_id:
        is_team_member = scan.target.group.team_id in [t.id for t in user.teams]
        
    if not is_owner and not is_team_member:
        return jsonify({'error': 'Access denied'}), 403
        
    return jsonify({
        'id': scan.id, 
        'target_id': scan.target_id, 
        'scan_type': scan.scan_type, 
        'status': scan.status,
        'started_at': scan.started_at,
        'completed_at': scan.completed_at,
        'raw_output': scan.raw_output,
        'user_id': scan.user_id
    })

@scan_bp.route('/', methods=['POST'])
@jwt_required()
def create_scan():
    data = request.get_json()
    if not data or 'target_id' not in data or 'scan_type' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    from flask import current_app
    from api.services.scan_manager import ScanManager
    
    current_user_id = get_jwt_identity()
    
    # Initialize ScanManager with current app
    # In a real app, this should probably be a singleton or initialized in app context
    scan_manager = ScanManager(current_app._get_current_object())
    
    # Extract OpenVAS config if provided
    openvas_config_id = data.get('openvas_config_id')
    
    scan_id = scan_manager.start_scan(
        data['target_id'], 
        data['scan_type'], 
        data.get('args'),
        openvas_config_id=openvas_config_id,
        user_id=current_user_id
    )
    
    return jsonify({'message': 'Scan started', 'scan_id': scan_id}), 201

@scan_bp.route('/<int:scan_id>/progress', methods=['GET'])
def get_scan_progress(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    
    # Calculate elapsed time
    elapsed = 0
    if scan.started_at:
        from datetime import datetime
        elapsed = int((datetime.utcnow() - scan.started_at).total_seconds())
    
    return jsonify({
        'id': scan.id,
        'status': scan.status,
        'progress': scan.progress or 0,
        'current_step': scan.current_step or 'Initializing...',
        'eta_seconds': scan.eta_seconds,
        'elapsed_seconds': elapsed,
        'target_name': scan.target.name if scan.target else 'Unknown',
        'vuln_count': scan.vuln_count or 0,
        'vuln_breakdown': scan.vuln_breakdown or {}
    })

@scan_bp.route('/<int:scan_id>/cancel', methods=['DELETE'])
def cancel_scan(scan_id):
    scan = Scan.query.get_or_404(scan_id)
    
    # Only allow cancellation of running scans
    if scan.status != 'running':
        return jsonify({'error': 'Can only cancel running scans'}), 400
    
    from flask import current_app
    from api.services.scan_manager import ScanManager
    
    scan_manager = ScanManager(current_app._get_current_object())
    
    if scan_manager.cancel_scan(scan_id):
        return jsonify({'message': 'Scan cancellation requested'}), 200
    else:
        return jsonify({'error': 'Scan not found in active scans'}), 404

@scan_bp.route('/queue/status', methods=['GET'])
def get_queue_status():
    """Get current queue status and active scans"""
    from flask import current_app
    from api.services.scan_manager import ScanManager
    
    scan_manager = ScanManager(current_app._get_current_object())
    
    # Get active scans
    active_scan_ids = list(scan_manager.active_scans.keys())
    active_scans = Scan.query.filter(Scan.id.in_(active_scan_ids)).all() if active_scan_ids else []
    
    # Get queued scans
    queued_scans = Scan.query.filter_by(status='queued').order_by(Scan.queue_position).all()
    
    return jsonify({
        'max_concurrent': scan_manager.scan_queue.max_concurrent,
        'active_count': len(active_scan_ids),
        'queue_size': scan_manager.scan_queue.get_queue_size(),
        'active_scans': [{
            'id': s.id,
            'target_name': s.target.name if s.target else 'Unknown',
            'scan_type': s.scan_type,
            'progress': s.progress or 0,
            'status': s.status
        } for s in active_scans],
        'queued_scans': [{
            'id': s.id,
            'target_name': s.target.name if s.target else 'Unknown',
            'scan_type': s.scan_type,
            'queue_position': s.queue_position,
            'status': s.status
        } for s in queued_scans]
    })

@scan_bp.route('/<int:id>', methods=['DELETE'])
def delete_scan(id):
    """Delete a scan report"""
    scan = Scan.query.get_or_404(id)
    
    # Prevent deletion of running scans
    if scan.status == 'running':
        return jsonify({'error': 'Cannot delete a running scan. Please cancel it first.'}), 400
    
    try:
        db.session.delete(scan)
        db.session.commit()
        return jsonify({'message': 'Scan deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
