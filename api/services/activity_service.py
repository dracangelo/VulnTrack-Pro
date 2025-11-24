from api.extensions import db
from api.models.activity_log import ActivityLog

class ActivityService:
    @staticmethod
    def log_activity(user_id, action, target_type, target_id, details=None):
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
        except Exception as e:
            print(f"Failed to log activity: {e}")
