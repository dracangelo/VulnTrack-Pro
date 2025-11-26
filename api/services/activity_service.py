from api.extensions import db
from api.models.activity_log import ActivityLog

class ActivityService:
    @staticmethod
    def log_activity(user_id, action, target_type=None, target_id=None, details=None):
        """
        Log a user or system activity.
        """
        try:
            log = ActivityLog(
                user_id=user_id,
                action=action,
                target_type=target_type,
                target_id=target_id,
                details=details
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            print(f"Failed to log activity: {e}")
            db.session.rollback()
            return None

    @staticmethod
    def get_recent_activity(limit=50):
        """
        Get recent activity logs.
        """
        return ActivityLog.query.order_by(ActivityLog.timestamp.desc()).limit(limit).all()
