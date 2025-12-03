from api.extensions import db
from datetime import datetime

class TargetGroup(db.Model):
    __tablename__ = 'target_groups'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    targets = db.relationship('Target', backref='group', lazy=True)

class Target(db.Model):
    __tablename__ = 'targets'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False) # IPv4 or IPv6
    description = db.Column(db.String(255))
    group_id = db.Column(db.Integer, db.ForeignKey('target_groups.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # OS Summary (latest detected)
    os_name = db.Column(db.String(255))
    os_cpe = db.Column(db.Text)
    os_last_detected = db.Column(db.DateTime)

    scans = db.relationship('Scan', back_populates='target', lazy=True)
    assets = db.relationship('AssetInventory', back_populates='target', lazy=True)
