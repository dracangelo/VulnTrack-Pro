from flask import Blueprint, jsonify, request
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.extensions import db

vuln_bp = Blueprint('vulnerabilities', __name__, url_prefix='/api/vulns')

@vuln_bp.route('/', methods=['GET'])
def get_vulns():
    """Get all vulnerability definitions with optional filtering"""
    severity = request.args.get('severity')
    search = request.args.get('search')
    
    query = Vulnerability.query
    
    if severity:
        query = query.filter_by(severity=severity)
    
    if search:
        query = query.filter(Vulnerability.name.ilike(f'%{search}%'))
    
    vulns = query.all()
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'severity': v.severity,
        'cvss_score': v.cvss_score,
        'description': v.description,
        'cve_id': v.cve_id,
        'category': v.category
    } for v in vulns])

@vuln_bp.route('/<int:vuln_id>', methods=['GET'])
def get_vuln(vuln_id):
    """Get a single vulnerability definition by ID"""
    vuln = Vulnerability.query.get_or_404(vuln_id)
    return jsonify({
        'id': vuln.id,
        'name': vuln.name,
        'severity': vuln.severity,
        'cvss_score': vuln.cvss_score,
        'cvss_vector': vuln.cvss_vector,
        'description': vuln.description,
        'cve_id': vuln.cve_id,
        'category': vuln.category,
        'remediation': vuln.remediation,
        'references': vuln.references
    })

@vuln_bp.route('/instances', methods=['GET'])
def get_instances():
    """
    Get vulnerability instances with comprehensive filtering.
    Query params:
    - target_id: Filter by target
    - group_id: Filter by target group
    - severity: Filter by severity (Critical, High, Medium, Low, Info)
    - status: Filter by status (open, fixed, false_positive, accepted_risk)
    - port: Filter by port number
    - protocol: Filter by protocol (tcp, udp)
    - search: Search in vulnerability name
    """
    target_id = request.args.get('target_id')
    group_id = request.args.get('group_id')
    severity = request.args.get('severity')
    status = request.args.get('status', 'open')  # Default to open
    port = request.args.get('port')
    protocol = request.args.get('protocol')
    search = request.args.get('search')
    
    # Join with Vulnerability and Target to enable filtering by group
    from api.models.target import Target
    query = VulnerabilityInstance.query.join(Vulnerability).join(Target)
    
    # Apply filters
    if target_id:
        query = query.filter(VulnerabilityInstance.target_id == target_id)
    
    if group_id:
        query = query.filter(Target.group_id == group_id)
    
    if severity:
        query = query.filter(Vulnerability.severity == severity)
    
    if status:
        query = query.filter(VulnerabilityInstance.status == status)
    
    if port:
        query = query.filter(VulnerabilityInstance.port == port)
    
    if protocol:
        query = query.filter(VulnerabilityInstance.protocol == protocol)
    
    if search:
        query = query.filter(Vulnerability.name.ilike(f'%{search}%'))
    
    # Order by severity (Critical first) and detection date
    severity_order = db.case(
        (Vulnerability.severity == 'Critical', 1),
        (Vulnerability.severity == 'High', 2),
        (Vulnerability.severity == 'Medium', 3),
        (Vulnerability.severity == 'Low', 4),
        (Vulnerability.severity == 'Info', 5),
        else_=6
    )
    query = query.order_by(severity_order, VulnerabilityInstance.detected_at.desc())
    
    instances = query.all()
    
    # Use the to_dict() method from the model
    return jsonify([i.to_dict() for i in instances])

@vuln_bp.route('/instances/<int:instance_id>', methods=['PATCH'])
def update_instance(instance_id):
    """Update vulnerability instance status"""
    instance = VulnerabilityInstance.query.get_or_404(instance_id)
    data = request.get_json()
    
    if 'status' in data:
        instance.status = data['status']
        
        # Set fixed_at timestamp if marking as fixed
        if data['status'] == 'fixed':
            from datetime import datetime
            instance.fixed_at = datetime.utcnow()
    
    if 'false_positive_reason' in data:
        instance.false_positive_reason = data['false_positive_reason']
    
    db.session.commit()
    
    db.session.commit()
    
    return jsonify(instance.to_dict())

# Bulk Operations
from api.services.bulk_service import BulkService

@vuln_bp.route('/bulk/status', methods=['POST'])
def bulk_update_status():
    data = request.get_json()
    vuln_ids = data.get('vuln_ids', [])
    status = data.get('status')
    reason = data.get('false_positive_reason')
    
    if not vuln_ids or not status:
        return jsonify({'error': 'Missing vuln_ids or status'}), 400
        
    count = BulkService.bulk_update_vuln_status(vuln_ids, status, reason)
    return jsonify({'message': f'Updated {count} vulnerabilities'}), 200

@vuln_bp.route('/bulk/ticket', methods=['POST'])
def bulk_create_tickets():
    data = request.get_json()
    vuln_ids = data.get('vuln_ids', [])
    ticket_data = data.get('ticket_data', {})
    
    if not vuln_ids:
        return jsonify({'error': 'No vuln_ids provided'}), 400
        
    ticket_ids = BulkService.bulk_create_tickets(vuln_ids, ticket_data)
    return jsonify({'message': f'Created {len(ticket_ids)} tickets', 'ticket_ids': ticket_ids}), 201
