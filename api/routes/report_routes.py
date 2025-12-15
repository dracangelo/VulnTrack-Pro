from flask import Blueprint, jsonify, request, Response, send_file
from io import BytesIO
from api.models.report import Report
from api.models.scan import Scan
from api.extensions import db
from datetime import datetime

# New advanced report generator (from package)
from api.services.report_generator import ReportGenerator as NewReportGenerator
# Old/legacy report generator (from legacy file)
from api.services.legacy_report_generator import ReportGenerator as OldReportGenerator

report_bp = Blueprint('reports', __name__, url_prefix='/api/reports')

@report_bp.route('/generate', methods=['POST'])
def generate_advanced_report():
    """
    Generate advanced reports with multiple types and formats.
    
    Expected JSON:
    {
        "type": "executive|technical|compliance|trend|comparison",
        "format": "excel|html|markdown|pdf|csv|json",
        "filters": {
            "scan_ids": [1, 2, 3],
            "severity": ["critical", "high"],
            "date_range": {"start": "2024-01-01", "end": "2024-12-31"}
        },
        "compliance_standard": "pci-dss|hipaa|soc2",  // for compliance reports
        "period_days": 30,  // for trend reports
        "scan_a_id": 1,  // for comparison reports
        "scan_b_id": 2   // for comparison reports
    }
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    report_type = data.get('type', 'technical')
    export_format = data.get('format', 'pdf')
    filters = data.get('filters', {})
    
    # Extract additional parameters
    kwargs = {}
    if report_type == 'compliance':
        kwargs['compliance_standard'] = data.get('compliance_standard', 'pci-dss')
    elif report_type == 'trend':
        kwargs['period_days'] = data.get('period_days', 30)
    elif report_type == 'comparison':
        kwargs['scan_a_id'] = data.get('scan_a_id')
        kwargs['scan_b_id'] = data.get('scan_b_id')
    
    try:
        # Generate report
        report_data, content_type = NewReportGenerator.generate(
            report_type=report_type,
            export_format=export_format,
            filters=filters,
            **kwargs
        )
        
        # Determine filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        extensions = {
            'excel': 'xlsx',
            'html': 'html',
            'markdown': 'md',
            'pdf': 'pdf',
            'csv': 'csv',
            'json': 'json'
        }
        ext = extensions.get(export_format, 'txt')
        filename = f"{report_type}_report_{timestamp}.{ext}"
        
        # Return file
        if isinstance(report_data, BytesIO):
            return send_file(
                report_data,
                mimetype=content_type,
                as_attachment=True,
                download_name=filename
            )
        else:
            # String data (HTML, Markdown, CSV, JSON)
            return send_file(
                BytesIO(report_data.encode('utf-8')),
                mimetype=content_type,
                as_attachment=True,
                download_name=filename
            )
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

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
        content = OldReportGenerator.generate_html_report(scan_id)
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
        pdf_content = OldReportGenerator.generate_pdf_report(scan_id)
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
    from api.models.target import Target
    
    target_id = request.args.get('target_id', type=int)
    vuln_manager = VulnManager()
    
    # Get severity counts using the new method
    severity_counts = vuln_manager.get_vulnerabilities_by_severity(target_id=target_id)
    
    # Get top vulnerable hosts (always global)
    top_hosts = vuln_manager.get_top_vulnerable_hosts(limit=5)
    
    # Get selected host information if target_id is provided
    selected_host = None
    if target_id:
        target = Target.query.get(target_id)
        if target:
            selected_host = {
                'id': target.id,
                'name': target.name,
                'ip_address': target.ip_address,
                'count': sum(severity_counts.values())
            }
    
    return jsonify({
        'severity_counts': severity_counts,
        'top_vulnerable_hosts': top_hosts,
        'selected_host': selected_host
    })

@report_bp.route('/scan/<int:scan_id>/pdf', methods=['GET'])
def download_scan_report_pdf(scan_id):
    try:
        pdf_bytes = OldReportGenerator.generate_pdf_report(scan_id)
        if not pdf_bytes:
            return jsonify({'error': 'Report generation failed or scan not found'}), 404
            
        return send_file(
            BytesIO(pdf_bytes),
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'scan_report_{scan_id}.pdf'
        )
    except RuntimeError as e:
        return jsonify({'error': str(e)}), 500
    except Exception as e:
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@report_bp.route('/scans/<int:scan_id>/download-pdf', methods=['GET'])
def download_scan_pdf(scan_id):
    """Download PDF report for a scan with database caching"""
    scan = Scan.query.get_or_404(scan_id)
    
    # Check if PDF already exists in database
    if scan.report_pdf:
        pdf_data = scan.report_pdf
    else:
        # Generate PDF on-demand
        pdf_data = OldReportGenerator.generate_pdf_report(scan_id)
        
        if not pdf_data:
            return jsonify({'error': 'Failed to generate PDF'}), 500
        
        # Store for future use
        try:
            scan.report_pdf = pdf_data
            db.session.commit()
        except Exception as e:
            print(f"Error storing PDF: {e}")
            # Continue anyway, we can still send the PDF
    
    # Send PDF file
    target_name = scan.target.name if scan.target else 'unknown'
    filename = f'scan_report_{scan_id}_{target_name}.pdf'.replace(' ', '_')
    
    return send_file(
        BytesIO(pdf_data),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )
