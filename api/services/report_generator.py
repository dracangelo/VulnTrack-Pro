from flask import render_template
from api.models.scan import Scan
from api.models.vulnerability import VulnerabilityInstance

class ReportGenerator:
    @staticmethod
    def generate_html_report(scan_id):
        scan = Scan.query.get(scan_id)
        if not scan:
            return None
            
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        # Render HTML report using external Jinja2 template
        return render_template('report.html', scan=scan, vulns=vulns)

    @staticmethod
    def generate_pdf_report(scan_id):
        scan = Scan.query.get(scan_id)
        if not scan:
            return None
            
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        # Generate PDF using WeasyPrint (pure Python)
        try:
            from weasyprint import HTML
        except ImportError:
            # If WeasyPrint is not installed, raise a clear error
            raise RuntimeError('WeasyPrint library is required for PDF generation. Install it via pip.')
        
        # Render the same HTML used for the report
        html_content = render_template('report.html', scan=scan, vulns=vulns)
        
        # Convert HTML to PDF bytes
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
