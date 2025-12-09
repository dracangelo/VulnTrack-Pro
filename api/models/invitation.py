from api.extensions import db
from datetime import datetime
import uuid

class TeamInvitation(db.Model):
    """
    Represents an invitation to join a team.
    """
    __tablename__ = 'team_invitations'

    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    email = db.Column(db.String(120), nullable=True) # Optional, if sent via email
    token = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    status = db.Column(db.String(20), default='pending') # pending, accepted, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True) # Optional expiration

    # Relationships
    team = db.relationship('Team', backref=db.backref('invitations', lazy=True))
    inviter = db.relationship('User', backref=db.backref('sent_invitations', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'team_id': self.team_id,
            'team_name': self.team.name,
            'inviter_id': self.inviter_id,
            'inviter_username': self.inviter.username,
            'email': self.email,
            'token': self.token,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }
