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
    """Get vulnerability statistics for dashboard"""
    from api.services.vuln_manager import VulnManager
    
    vuln_manager = VulnManager()
    
    # Get severity counts using the new method
    severity_counts = vuln_manager.get_vulnerabilities_by_severity()
    
    # Get top vulnerable hosts
    top_hosts = vuln_manager.get_top_vulnerable_hosts(limit=5)
    
    return jsonify({
        'severity_counts': severity_counts,
        'top_vulnerable_hosts': top_hosts
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
