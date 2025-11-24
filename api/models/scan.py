from api.extensions import db
from datetime import datetime

class Scan(db.Model):
    __tablename__ = 'scans'

    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False) # 'nmap', 'openvas', 'custom'
    status = db.Column(db.String(20), default='pending') # pending, running, completed, failed
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    raw_output = db.Column(db.Text) # JSON or text output
    
    vulnerabilities = db.relationship('VulnerabilityInstance', backref='scan', lazy=True)
