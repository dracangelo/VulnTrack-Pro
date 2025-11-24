from flask import render_template_string
from api.models.scan import Scan
from api.models.vulnerability import VulnerabilityInstance

class ReportGenerator:
    @staticmethod
    def generate_html_report(scan_id):
        scan = Scan.query.get(scan_id)
        if not scan:
            return None
            
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        # Basic HTML Template
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Scan Report #{{ scan.id }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                h1 { color: #333; }
                .meta { margin-bottom: 20px; color: #666; }
                table { width: 100%; border-collapse: collapse; margin-top: 20px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #f2f2f2; }
                .severity-Critical { color: red; font-weight: bold; }
                .severity-High { color: orange; font-weight: bold; }
                .severity-Medium { color: #d4d400; }
                .severity-Low { color: green; }
                .severity-Info { color: blue; }
            </style>
        </head>
        <body>
            <h1>Vulnerability Scan Report</h1>
            <div class="meta">
                <p><strong>Scan ID:</strong> {{ scan.id }}</p>
                <p><strong>Target:</strong> {{ scan.target.name }} ({{ scan.target.ip_address }})</p>
                <p><strong>Date:</strong> {{ scan.completed_at }}</p>
                <p><strong>Status:</strong> {{ scan.status }}</p>
            </div>
            
            <h2>Findings</h2>
            <table>
                <thead>
                    <tr>
                        <th>Vulnerability</th>
                        <th>Severity</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vuln in vulns %}
                    <tr>
                        <td>
                            <strong>{{ vuln.vulnerability.name }}</strong><br>
                            <small>{{ vuln.vulnerability.description }}</small>
                        </td>
                        <td class="severity-{{ vuln.vulnerability.severity }}">{{ vuln.vulnerability.severity }}</td>
                        <td>{{ vuln.status }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </body>
        </html>
        """
        
        return render_template_string(template, scan=scan, vulns=vulns)

    @staticmethod
    def generate_pdf_report(scan_id):
        scan = Scan.query.get(scan_id)
        if not scan:
            return None
            
        vulns = VulnerabilityInstance.query.filter_by(scan_id=scan_id).all()
        
        from fpdf import FPDF
        from io import BytesIO
        
        class PDF(FPDF):
            def header(self):
                self.set_font('Arial', 'B', 15)
                self.cell(0, 10, f'Vulnerability Scan Report #{scan_id}', 0, 1, 'C')
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font('Arial', 'I', 8)
                self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

        pdf = PDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Meta Info
        pdf.cell(0, 10, f"Target: {scan.target.name} ({scan.target.ip_address})", 0, 1)
        pdf.cell(0, 10, f"Date: {scan.completed_at}", 0, 1)
        pdf.cell(0, 10, f"Status: {scan.status}", 0, 1)
        pdf.ln(10)
        
        # Findings
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(0, 10, "Findings", 0, 1)
        pdf.set_font("Arial", size=12)
        
        for vuln in vulns:
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(0, 10, f"{vuln.vulnerability.name} ({vuln.vulnerability.severity})", 0, 1)
            pdf.set_font("Arial", size=10)
            pdf.multi_cell(0, 5, f"Description: {vuln.vulnerability.description}")
            pdf.ln(5)
            
        # Output to buffer
        # FPDF output() returns a string in Py2, bytes in Py3 if dest='S'. 
        # Actually in recent FPDF, output(dest='S') returns bytes.
        # Let's use output() which returns string/bytes and encode if needed or write to BytesIO.
        # FPDF class doesn't support writing directly to BytesIO easily in all versions.
        # Standard way: pdf.output(dest='S').encode('latin-1')
        
        try:
            return pdf.output(dest='S').encode('latin-1')
        except:
            # Fallback for newer fpdf2 or different versions
            return pdf.output()
