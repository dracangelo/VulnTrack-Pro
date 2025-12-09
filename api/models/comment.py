from api.extensions import db
from datetime import datetime

class Comment(db.Model):
    """
    Represents a comment on a resource (Vulnerability, Ticket, etc.).
    """
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Resource Links (Nullable FKs to support polymorphism-like behavior)
    vulnerability_instance_id = db.Column(db.Integer, db.ForeignKey('vulnerability_instances.id'), nullable=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('tickets.id'), nullable=True)
    
    # Threading
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)
    
    # Relationships
    user = db.relationship('User', backref='comments')
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.username if self.user else 'Unknown',
            'text': self.text,
            'created_at': self.created_at.isoformat(),
            'parent_id': self.parent_id,
            'reply_count': self.replies.count()
        }
