from api.extensions import db
from datetime import datetime
import uuid

class Invite(db.Model):
    __tablename__ = 'invites'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_used = db.Column(db.Boolean, default=False)
    
    # Relationships
    role = db.relationship('Role', backref='invites')
    creator = db.relationship('User', backref='created_invites')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role.name if self.role else 'Unknown',
            'expires_at': self.expires_at.isoformat(),
            'created_by': self.creator.username if self.creator else 'Unknown',
            'created_at': self.created_at.isoformat(),
            'is_used': self.is_used
        }
