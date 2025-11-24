from api.extensions import db
from datetime import datetime

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    
    # Scan configuration
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    scan_type = db.Column(db.String(50), nullable=False)  # 'nmap', 'openvas', etc.
    scanner_args = db.Column(db.String(500))  # Nmap arguments or other scanner args
    openvas_config_id = db.Column(db.String(255))  # Optional OpenVAS config
    
    # Schedule configuration
    cron_expression = db.Column(db.String(100), nullable=False)  # e.g., "0 2 * * *"
    next_run = db.Column(db.DateTime)  # Next scheduled run time
    last_run = db.Column(db.DateTime)  # Last execution time
    
    # Status
    enabled = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    target = db.relationship('Target', backref='schedules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_id': self.target_id,
            'target_name': self.target.name if self.target else None,
            'scan_type': self.scan_type,
            'scanner_args': self.scanner_args,
            'openvas_config_id': self.openvas_config_id,
            'cron_expression': self.cron_expression,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
