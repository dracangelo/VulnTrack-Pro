from api.extensions import db
from datetime import datetime

class DashboardConfig(db.Model):
    """
    Stores user-specific dashboard configurations.
    Allows users to save their preferred layout and widget settings.
    """
    __tablename__ = 'dashboard_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), default='Default Dashboard')
    is_default = db.Column(db.Boolean, default=False)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id'), nullable=True) # For shared dashboards
    
    # JSON blob to store the layout configuration
    # Example:
    # {
    #   "widgets": [
    #     {"id": "vuln_timeline", "x": 0, "y": 0, "w": 12, "h": 4, "settings": {"days": 30}},
    #     {"id": "risk_heatmap", "x": 0, "y": 4, "w": 6, "h": 4, "settings": {}}
    #   ]
    # }
    layout_data = db.Column(db.JSON, nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('dashboard_configs', lazy=True))
    team = db.relationship('Team', backref='shared_dashboards')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'is_default': self.is_default,
            'layout_data': self.layout_data,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }
