from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.scan import Scan

scan_bp = Blueprint('scans', __name__, url_prefix='/api/scans')

@scan_bp.route('/', methods=['GET'])
def get_scans():
    scans = Scan.query.order_by(Scan.id.desc()).limit(20).all()
    return jsonify([{
        'id': s.id, 
        'target_id': s.target_id,
        'target_name': s.target.name if s.target else 'Unknown',
        'scan_type': s.scan_type, 
        'status': s.status,
        'created_at': s.started_at.isoformat() if s.started_at else None,
        'completed_at': s.completed_at.isoformat() if s.completed_at else None
    } for s in scans])

@scan_bp.route('/<int:id>', methods=['GET'])
def get_scan(id):
    scan = Scan.query.get_or_404(id)
    return jsonify({
        'id': scan.id, 
        'target_id': scan.target_id, 
        'scan_type': scan.scan_type, 
        'status': scan.status,
        'started_at': scan.started_at,
        'completed_at': scan.completed_at,
        'raw_output': scan.raw_output
    })

@scan_bp.route('/', methods=['POST'])
def create_scan():
    data = request.get_json()
    if not data or 'target_id' not in data or 'scan_type' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    from flask import current_app
    from api.services.scan_manager import ScanManager
    
    # Initialize ScanManager with current app
    # In a real app, this should probably be a singleton or initialized in app context
    scan_manager = ScanManager(current_app._get_current_object())
    
    scan_id = scan_manager.start_scan(data['target_id'], data['scan_type'], data.get('args'))
    
    return jsonify({'message': 'Scan started', 'scan_id': scan_id}), 201
