"""
Report Generator Package.
Main entry point for generating reports.
"""
from typing import Dict, Any, Optional
from io import BytesIO
from api.services.report_generator.base_report import BaseReport
from api.services.report_generator.executive_report import ExecutiveReport
from api.services.report_generator.technical_report import TechnicalReport
from api.services.report_generator.compliance_report import ComplianceReport
from api.services.report_generator.trend_report import TrendReport
from api.services.report_generator.comparison_report import ComparisonReport
from api.services.report_generator.exporters import ExcelExporter, HTMLExporter, MarkdownExporter


class ReportGenerator:
    """
    Main report generator class.
    Coordinates report generation and export.
    """
    
    REPORT_TYPES = {
        'executive': ExecutiveReport,
        'technical': TechnicalReport,
        'compliance': ComplianceReport,
        'trend': TrendReport,
        'comparison': ComparisonReport,
    }
    
    EXPORTERS = {
        'excel': ExcelExporter,
        'html': HTMLExporter,
        'markdown': MarkdownExporter,
    }
    
    @classmethod
    def generate(cls, report_type: str, export_format: str, filters: Optional[Dict[str, Any]] = None, **kwargs):
        """
        Generate a report.
        
        Args:
            report_type: Type of report ('executive', 'technical', 'compliance', 'trend', 'comparison')
            export_format: Export format ('excel', 'html', 'markdown', 'pdf', 'csv', 'json')
            filters: Optional filters for data
            **kwargs: Additional parameters:
                - compliance_standard: For compliance reports ('pci-dss', 'hipaa', 'soc2')
                - period_days: For trend reports (default: 30)
                - scan_a_id: For comparison reports (baseline scan)
                - scan_b_id: For comparison reports (comparison scan)
            
        Returns:
            Report data in requested format
            
        Raises:
            ValueError: If report type or format is invalid
        """
        # Validate report type
        if report_type not in cls.REPORT_TYPES:
            raise ValueError(f"Invalid report type: {report_type}. Must be one of: {list(cls.REPORT_TYPES.keys())}")
        
        # Create report instance with appropriate parameters
        report_class = cls.REPORT_TYPES[report_type]
        
        if report_type == 'compliance':
            compliance_standard = kwargs.get('compliance_standard', 'pci-dss')
            report = report_class(filters=filters, compliance_standard=compliance_standard)
        elif report_type == 'trend':
            period_days = kwargs.get('period_days', 30)
            report = report_class(filters=filters, period_days=period_days)
        elif report_type == 'comparison':
            scan_a_id = kwargs.get('scan_a_id')
            scan_b_id = kwargs.get('scan_b_id')
            if not scan_a_id or not scan_b_id:
                raise ValueError("Comparison reports require scan_a_id and scan_b_id parameters")
            report = report_class(scan_a_id=scan_a_id, scan_b_id=scan_b_id)
        else:
            report = report_class(filters=filters)
        
        # Gather data
        data = report.gather_data()
        
        # Export based on format
        if export_format == 'excel':
            exporter = ExcelExporter()
            return exporter.export(data), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        
        elif export_format == 'html':
            exporter = HTMLExporter()
            return exporter.export(data), 'text/html'
        
        elif export_format == 'markdown':
            exporter = MarkdownExporter()
            return exporter.export(data), 'text/markdown'
        
        elif export_format == 'json':
            import json
            return json.dumps(data, indent=2, default=str), 'application/json'
        
        elif export_format == 'csv':
            return cls._export_csv(data), 'text/csv'
        
        elif export_format == 'pdf':
            # Use existing PDF generation (if available)
            return cls._export_pdf(data), 'application/pdf'
        
        else:
            raise ValueError(f"Invalid export format: {export_format}")
    
    @classmethod
    def _export_csv(cls, data: Dict[str, Any]) -> str:
        """Export to CSV format."""
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Name', 'Severity', 'CVSS', 'CVE', 'Target', 'Status'])
        
        # Write data
        for vuln in data.get('vulnerabilities', []):
            writer.writerow([
                vuln.get('name', ''),
                vuln.get('severity', ''),
                vuln.get('cvss_score', ''),
                vuln.get('cve_id', ''),
                vuln.get('target', ''),
                vuln.get('status', '')
            ])
        
        return output.getvalue()
    
    @classmethod
    def _export_pdf(cls, data: Dict[str, Any]) -> BytesIO:
        """Export to PDF format (placeholder - use existing PDF generator)."""
        # This would integrate with existing PDF generation
        # For now, return a simple message
        from io import BytesIO
        return BytesIO(b"PDF export - integrate with existing PDF generator")


__all__ = ['ReportGenerator', 'ExecutiveReport', 'TechnicalReport', 'ComplianceReport', 'TrendReport', 'ComparisonReport']
