from api.extensions import db
from datetime import datetime

class AssetInventory(db.Model):
    """Store enriched asset information including OS, services, and banners"""
    __tablename__ = 'asset_inventory'
    
    id = db.Column(db.Integer, primary_key=True)
    target_id = db.Column(db.Integer, db.ForeignKey('targets.id'), nullable=False)
    scan_id = db.Column(db.Integer, db.ForeignKey('scans.id'), nullable=True)
    
    # OS Information
    os_name = db.Column(db.String(255))
    os_vendor = db.Column(db.String(255))
    os_family = db.Column(db.String(100))
    os_accuracy = db.Column(db.Integer)  # Percentage (0-100)
    os_cpe = db.Column(db.Text)  # CPE identifier for OS
    
    # Service Information (per port)
    port = db.Column(db.Integer, nullable=False)
    protocol = db.Column(db.String(10))  # tcp/udp
    service_name = db.Column(db.String(100))
    service_product = db.Column(db.String(255))
    service_version = db.Column(db.String(100))
    service_extrainfo = db.Column(db.String(255))
    service_cpe = db.Column(db.Text)  # CPE identifier for service
    
    # Banner Information
    banner = db.Column(db.Text)
    banner_grabbed_at = db.Column(db.DateTime)
    
    # Metadata
    discovered_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    target = db.relationship('Target', back_populates='assets')
    scan = db.relationship('Scan', backref='discovered_assets')
    
    def to_dict(self):
        """Convert asset to dictionary for API responses"""
        return {
            'id': self.id,
            'target_id': self.target_id,
            'scan_id': self.scan_id,
            'os': {
                'name': self.os_name,
                'vendor': self.os_vendor,
                'family': self.os_family,
                'accuracy': self.os_accuracy,
                'cpe': self.os_cpe
            } if self.os_name else None,
            'service': {
                'port': self.port,
                'protocol': self.protocol,
                'name': self.service_name,
                'product': self.service_product,
                'version': self.service_version,
                'extrainfo': self.service_extrainfo,
                'cpe': self.service_cpe
            },
            'banner': self.banner,
            'banner_grabbed_at': self.banner_grabbed_at.isoformat() if self.banner_grabbed_at else None,
            'discovered_at': self.discovered_at.isoformat() if self.discovered_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }
