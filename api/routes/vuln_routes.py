from flask import Blueprint, jsonify, request
from api.models.vulnerability import Vulnerability, VulnerabilityInstance

vuln_bp = Blueprint('vulnerabilities', __name__, url_prefix='/api/vulns')

@vuln_bp.route('/', methods=['GET'])
def get_vulns():
    vulns = Vulnerability.query.all()
    return jsonify([{
        'id': v.id,
        'name': v.name,
        'severity': v.severity,
        'description': v.description,
        'cve_id': v.cve_id
    } for v in vulns])

@vuln_bp.route('/instances', methods=['GET'])
def get_instances():
    target_id = request.args.get('target_id')
    severity = request.args.get('severity')
    
    query = VulnerabilityInstance.query
    
    if target_id:
        query = query.filter_by(target_id=target_id)
        
    if severity:
        query = query.join(Vulnerability).filter(Vulnerability.severity == severity)
        
    instances = query.all()
    return jsonify([{
        'id': i.id,
        'vulnerability_id': i.vulnerability_id,
        'scan_id': i.scan_id,
        'target_id': i.target_id,
        'status': i.status,
        'vulnerability_name': i.vulnerability.name,
        'severity': i.vulnerability.severity
    } for i in instances])
