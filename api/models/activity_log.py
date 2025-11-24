from api.extensions import db
from datetime import datetime

class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Nullable for system actions
    action = db.Column(db.String(50), nullable=False) # e.g., 'create_ticket', 'start_scan'
    target_type = db.Column(db.String(50)) # e.g., 'Ticket', 'Scan'
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text) # JSON or text details
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='activities')
