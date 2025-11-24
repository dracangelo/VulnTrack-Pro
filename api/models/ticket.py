from api.extensions import db
from datetime import datetime

class Ticket(db.Model):
    __tablename__ = 'tickets'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='open') # open, in_progress, closed
    priority = db.Column(db.String(20), default='medium')
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    assignee = db.relationship('User', backref='assigned_tickets')
    
    # Many-to-Many relationship with VulnerabilityInstance
    vulnerabilities = db.relationship('VulnerabilityInstance', secondary='ticket_vulnerabilities', backref='tickets')

# Association Table
ticket_vulnerabilities = db.Table('ticket_vulnerabilities',
    db.Column('ticket_id', db.Integer, db.ForeignKey('tickets.id'), primary_key=True),
    db.Column('vulnerability_instance_id', db.Integer, db.ForeignKey('vulnerability_instances.id'), primary_key=True)
)
