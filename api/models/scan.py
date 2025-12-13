from api.extensions import db
from datetime import datetime

class Scan(db.Model):
    __tablename__ = 'scans'
    # Store generated reports
    report_html = db.Column(db.Text)  # HTML report content
    report_pdf = db.Column(db.LargeBinary)  # PDF binary data

    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Owner of the scan
    scan_type = db.Column(db.String(50), nullable=False) # 'nmap', 'openvas', 'custom'
    status = db.Column(db.String(50), default='pending') # pending, running, completed, failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    raw_output = db.Column(db.Text) # JSON or text output
    
    # Progress tracking
    progress = db.Column(db.Integer, default=0)  # 0-100
    current_step = db.Column(db.String(255))
    eta_seconds = db.Column(db.Integer)
    
    # OpenVAS integration
    openvas_task_id = db.Column(db.String(255))
    openvas_report_id = db.Column(db.String(255))
    openvas_config_id = db.Column(db.String(255))  # Selected OpenVAS scan config
    
    # Vulnerability tracking
    vuln_count = db.Column(db.Integer, default=0)
    vuln_breakdown = db.Column(db.JSON)  # {"Critical": 2, "High": 5, ...}
    
    # Queue management
    queue_position = db.Column(db.Integer, default=0)  # 0 = not queued/running
    
    target = db.relationship('Target', back_populates='scans')
