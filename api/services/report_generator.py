from flask import render_template
from api.models.scan import Scan
from api.models.vulnerability import VulnerabilityInstance
from datetime import datetime

class ReportGenerator:
    @staticmethod
    def generate_html_report(scan_id):
        """Generate HTML report for a scan"""
        scan = Scan.query.get(scan_id)
        if not scan:
            return None
            
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        # Group vulnerabilities by severity
        vuln_by_severity = {
            'Critical': [],
            'High': [],
            'Medium': [],
            'Low': [],
            'Info': []
        }
        
        for vuln in vulns:
            severity = vuln.vulnerability.severity if vuln.vulnerability else 'Info'
            if severity in vuln_by_severity:
                vuln_by_severity[severity].append(vuln)
        
        # Render HTML report using external Jinja2 template
        return render_template('report.html', 
                             scan=scan, 
                             vulns=vulns,
                             vuln_by_severity=vuln_by_severity,
                             generated_at=datetime.utcnow())

    @staticmethod
    def generate_pdf_report(scan_id):
        """
        Generate PDF report with proper styling
        Returns: PDF bytes or None on error
        """
        scan = Scan.query.get(scan_id)
        if not scan:
            print(f"Scan {scan_id} not found")
            return None
            
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
        except ImportError as e:
            print(f"WeasyPrint not installed: {e}")
            return None
        
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        # Group vulnerabilities by severity
        vuln_by_severity = {
            'Critical': [],
            'High': [],
            'Medium': [],
            'Low': [],
            'Info': []
        }
        
        for vuln in vulns:
            severity = vuln.vulnerability.severity if vuln.vulnerability else 'Info'
            if severity in vuln_by_severity:
                vuln_by_severity[severity].append(vuln)
        
        # Render HTML with PDF-specific template
        try:
            html_content = render_template('report_pdf.html', 
                                         scan=scan, 
                                         vulns=vulns,
                                         vuln_by_severity=vuln_by_severity,
                                         generated_at=datetime.utcnow())
        except Exception as e:
            print(f"Error rendering PDF template: {e}")
            # Fallback to regular HTML template
            html_content = render_template('report.html', 
                                         scan=scan, 
                                         vulns=vulns,
                                         vuln_by_severity=vuln_by_severity,
                                         generated_at=datetime.utcnow())
        
        # PDF-specific CSS for better formatting
        pdf_css = CSS(string='''
            @page {
                size: A4;
                margin: 2cm;
            }
            body {
                font-family: Arial, Helvetica, sans-serif;
                font-size: 10pt;
                line-height: 1.5;
                color: #333;
            }
            h1 { 
                font-size: 20pt; 
                color: #2c3e50; 
                margin-top: 0;
            }
            h2 { 
                font-size: 16pt; 
                color: #34495e; 
                page-break-after: avoid;
                margin-top: 20pt;
            }
            h3 { 
                font-size: 14pt; 
                color: #7f8c8d;
                page-break-after: avoid;
            }
            .page-break {
                page-break-after: always;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 10pt 0;
            }
            th, td {
                padding: 8pt;
                text-align: left;
                border-bottom: 1pt solid #ddd;
            }
            th {
                background-color: #34495e;
                color: white;
                font-weight: bold;
            }
            .vulnerability {
                margin: 15pt 0;
                padding: 10pt;
                border: 1pt solid #bdc3c7;
                page-break-inside: avoid;
            }
            .severity-critical { border-left: 4pt solid #e74c3c; }
            .severity-high { border-left: 4pt solid #e67e22; }
            .severity-medium { border-left: 4pt solid #f39c12; }
            .severity-low { border-left: 4pt solid #3498db; }
            .severity-info { border-left: 4pt solid #95a5a6; }
        ''')
        
        try:
            # Generate PDF with font configuration
            font_config = FontConfiguration()
            pdf_bytes = HTML(string=html_content).write_pdf(
                stylesheets=[pdf_css],
                font_config=font_config
            )
            
            return pdf_bytes
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None
