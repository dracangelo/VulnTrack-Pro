from flask import Blueprint, jsonify, request
from api.models.vulnerability import Vulnerability, VulnerabilityInstance
from api.models.target import Target
from api.extensions import db
from sqlalchemy import func

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/', methods=['GET'])
def get_reports():
    return jsonify({'message': 'List of reports'})

@report_bp.route('/stats', methods=['GET'])
def get_stats():
    from api.models.vulnerability import VulnerabilityInstance
    from api.models.target import Target
    from api.extensions import db
    from sqlalchemy import func

    # Vulnerabilities by severity
    severity_counts = db.session.query(
        VulnerabilityInstance.vulnerability.has(severity='Critical'),
        VulnerabilityInstance.vulnerability.has(severity='High'),
        VulnerabilityInstance.vulnerability.has(severity='Medium'),
        VulnerabilityInstance.vulnerability.has(severity='Low'),
        VulnerabilityInstance.vulnerability.has(severity='Info')
    ).all() # This logic is a bit complex for single query with has, let's do simple group by if possible or separate counts.
    
    # Simpler approach: Join and Group By
    # We need to join VulnerabilityInstance with Vulnerability
    stats = db.session.query(
        Vulnerability.severity, func.count(VulnerabilityInstance.id)
    ).join(VulnerabilityInstance).group_by(Vulnerability.severity).all()
    
    severity_data = {s[0]: s[1] for s in stats}
    
    # Most vulnerable hosts
    host_stats = db.session.query(
        Target.name, func.count(VulnerabilityInstance.id)
    ).join(VulnerabilityInstance).group_by(Target.id).order_by(func.count(VulnerabilityInstance.id).desc()).limit(5).all()
    
    host_data = [{'name': h[0], 'count': h[1]} for h in host_stats]
    
    return jsonify({
        'severity_counts': severity_data,
        'top_vulnerable_hosts': host_data
    })

@report_bp.route('/<int:scan_id>/download', methods=['GET'])
def download_report(scan_id):
    from api.services.report_generator import ReportGenerator
    from flask import Response
    
    fmt = request.args.get('format', 'html')
    
    if fmt == 'html':
        report_content = ReportGenerator.generate_html_report(scan_id)
        if not report_content:
            return jsonify({'error': 'Scan not found or report generation failed'}), 404
            
        return Response(
            report_content,
            mimetype="text/html",
            headers={"Content-disposition": f"attachment; filename=scan_report_{scan_id}.html"}
        )
    elif fmt == 'pdf':
        pdf_file = ReportGenerator.generate_pdf_report(scan_id)
        if not pdf_file:
            return jsonify({'error': 'PDF generation failed'}), 500
            
        return Response(
            pdf_file,
            mimetype="application/pdf",
            headers={"Content-disposition": f"attachment; filename=scan_report_{scan_id}.pdf"}
        )
    else:
        return jsonify({'error': 'Unsupported format'}), 400
