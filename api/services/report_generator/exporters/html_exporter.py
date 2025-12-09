"""
HTML exporter for reports.
Creates standalone HTML reports with embedded CSS and charts.
"""
from typing import Dict, List, Any
from jinja2 import Template


class HTMLExporter:
    """Export reports to standalone HTML format."""
    
    HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333; background: #f4f4f4; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px 20px; margin-bottom: 30px; border-radius: 8px; }
        h1 { font-size: 2.5em; margin-bottom: 10px; }
        .meta { font-size: 0.9em; opacity: 0.9; }
        .summary { background: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }
        .stat-card { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 2.5em; font-weight: bold; margin: 10px 0; }
        .stat-label { font-size: 0.9em; opacity: 0.9; text-transform: uppercase; }
        .severity-breakdown { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 20px 0; }
        .severity-badge { padding: 15px; border-radius: 6px; text-align: center; color: white; font-weight: bold; }
        .severity-critical { background: #c00000; }
        .severity-high { background: #ff6600; }
        .severity-medium { background: #ffc000; }
        .severity-low { background: #92d050; }
        .severity-info { background: #00b0f0; }
        table { width: 100%; background: white; border-collapse: collapse; margin: 20px 0; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        th { background: #667eea; color: white; padding: 15px; text-align: left; font-weight: 600; }
        td { padding: 12px 15px; border-bottom: 1px solid #e0e0e0; }
        tr:hover { background: #f8f9fa; }
        .badge { display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 0.85em; font-weight: bold; color: white; }
        .section { background: white; padding: 25px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h2 { color: #667eea; margin-bottom: 15px; padding-bottom: 10px; border-bottom: 2px solid #667eea; }
        @media print { body { background: white; } .container { max-width: 100%; } }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{{ title }}</h1>
            <div class="meta">Generated: {{ generated_at }}</div>
        </header>
        
        <div class="summary">
            <h2>Executive Summary</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Vulnerabilities</div>
                    <div class="stat-value">{{ summary_stats.total_vulnerabilities }}</div>
                </div>
                <div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                    <div class="stat-label">Critical & High</div>
                    <div class="stat-value">{{ summary_stats.critical_high_count }}</div>
                </div>
            </div>
            
            <h3 style="margin-top: 20px;">Severity Breakdown</h3>
            <div class="severity-breakdown">
                <div class="severity-badge severity-critical">
                    <div style="font-size: 1.5em;">{{ summary_stats.severity_counts.critical }}</div>
                    <div>Critical</div>
                </div>
                <div class="severity-badge severity-high">
                    <div style="font-size: 1.5em;">{{ summary_stats.severity_counts.high }}</div>
                    <div>High</div>
                </div>
                <div class="severity-badge severity-medium">
                    <div style="font-size: 1.5em;">{{ summary_stats.severity_counts.medium }}</div>
                    <div>Medium</div>
                </div>
                <div class="severity-badge severity-low">
                    <div style="font-size: 1.5em;">{{ summary_stats.severity_counts.low }}</div>
                    <div>Low</div>
                </div>
                <div class="severity-badge severity-info">
                    <div style="font-size: 1.5em;">{{ summary_stats.severity_counts.info }}</div>
                    <div>Info</div>
                </div>
            </div>
        </div>
        
        {% if vulnerabilities %}
        <div class="section">
            <h2>Vulnerability Details</h2>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Severity</th>
                        <th>CVSS</th>
                        <th>CVE</th>
                        <th>Target</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    {% for vuln in vulnerabilities %}
                    <tr>
                        <td><strong>{{ vuln.name }}</strong></td>
                        <td><span class="badge severity-{{ vuln.severity|lower }}">{{ vuln.severity|upper }}</span></td>
                        <td>{{ vuln.cvss_score or 'N/A' }}</td>
                        <td>{{ vuln.cve_id or 'N/A' }}</td>
                        <td>{{ vuln.target }}</td>
                        <td>{{ vuln.status or 'Open' }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
        
        {% if recommendations %}
        <div class="section">
            <h2>Recommendations</h2>
            <table>
                <thead>
                    <tr>
                        <th>Priority</th>
                        <th>Vulnerability</th>
                        <th>Recommendation</th>
                    </tr>
                </thead>
                <tbody>
                    {% for rec in recommendations %}
                    <tr>
                        <td><span class="badge severity-{{ rec.priority|lower }}">{{ rec.priority }}</span></td>
                        <td>{{ rec.vulnerability }}</td>
                        <td>{{ rec.recommendation }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
    """
    
    def export(self, data: Dict[str, Any]) -> str:
        """
        Export data to HTML format.
        
        Args:
            data: Complete report data
            
        Returns:
            HTML string
        """
        template = Template(self.HTML_TEMPLATE)
        return template.render(**data)
