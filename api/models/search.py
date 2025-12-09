from api.extensions import db
from datetime import datetime

class SavedSearch(db.Model):
    """
    Stores user saved searches and search history.
    """
    __tablename__ = 'saved_searches'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100))  # Optional name for saved filters
    query = db.Column(db.String(255))  # The search text
    filters = db.Column(db.JSON)  # Structured filters (e.g., {"severity": "High"})
    is_history = db.Column(db.Boolean, default=False)  # True if just history, False if explicitly saved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('saved_searches', lazy=True))

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'query': self.query,
            'filters': self.filters,
            'is_history': self.is_history,
            'created_at': self.created_at.isoformat()
        }
