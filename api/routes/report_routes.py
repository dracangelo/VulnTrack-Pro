from flask import Blueprint, jsonify, request, Response
from api.models.report import Report
from api.models.scan import Scan
from api.extensions import db
from api.services.report_generator import ReportGenerator
from datetime import datetime

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/', methods=['GET'])
def get_reports():
    reports = Report.query.order_by(Report.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reports])

@report_bp.route('/', methods=['POST'])
def create_report():
    data = request.get_json()
    scan_id = data.get('scan_id')
    report_type = data.get('type', 'scan') # 'scan' or 'manual'
    fmt = data.get('format', 'html')
    
    if not scan_id:
        return jsonify({'error': 'Scan ID is required'}), 400
        
    scan = Scan.query.get(scan_id)
    if not scan:
        return jsonify({'error': 'Scan not found'}), 404
        
    # Generate report content
    if fmt == 'html':
        content = ReportGenerator.generate_html_report(scan_id)
        if not content:
            return jsonify({'error': 'Failed to generate HTML report'}), 500
            
        report = Report(
            title=f"Scan Report - {scan.target.name}",
            type=report_type,
            format='html',
            status='completed',
            scan_id=scan_id,
            content=content
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify(report.to_dict()), 201
        
    elif fmt == 'pdf':
        pdf_content = ReportGenerator.generate_pdf_report(scan_id)
        if not pdf_content:
            return jsonify({'error': 'Failed to generate PDF report'}), 500
            
        report = Report(
            title=f"Scan Report - {scan.target.name}",
            type=report_type,
            format='pdf',
            status='completed',
            scan_id=scan_id,
            pdf_content=pdf_content
        )
        db.session.add(report)
        db.session.commit()
        
        return jsonify(report.to_dict()), 201
        
    else:
        return jsonify({'error': 'Unsupported format'}), 400

@report_bp.route('/<int:report_id>/download', methods=['GET'])
def download_report(report_id):
    report = Report.query.get(report_id)
    if not report:
        return jsonify({'error': 'Report not found'}), 404
        
    if report.format == 'html':
        return Response(
            report.content,
            mimetype="text/html",
            headers={"Content-disposition": f"attachment; filename=report_{report_id}.html"}
        )
    elif report.format == 'pdf':
        return Response(
            report.pdf_content,
            mimetype="application/pdf",
            headers={"Content-disposition": f"attachment; filename=report_{report_id}.pdf"}
        )
    else:
        return jsonify({'error': 'Unknown format'}), 400

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
