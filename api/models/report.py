from api.extensions import db
from datetime import datetime

class Report(db.Model):
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # 'scan', 'manual'
    format = db.Column(db.String(10), nullable=False)  # 'html', 'pdf'
    status = db.Column(db.String(50), default='pending')  # 'pending', 'completed', 'failed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Foreign Keys
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=True)
    
    # Content storage (similar to Scan model)
    file_path = db.Column(db.String(512), nullable=True)  # If stored on disk
    content = db.Column(db.Text, nullable=True)  # For HTML content
    pdf_content = db.Column(db.LargeBinary, nullable=True)  # For PDF content

    # Relationships
    scan = db.relationship('Scan', backref=db.backref('reports', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'report_type': self.type,
            'format': self.format,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'scan_id': self.scan_id,
            'scan_target': self.scan.target.name if self.scan and self.scan.target else None
        }
