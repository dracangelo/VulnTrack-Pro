"""
Collaboration Service.
Handles comments, activity feeds, and team interactions.
"""
from api.models.comment import Comment
from api.models.activity_log import ActivityLog
from api.models.team import Team
from api.models.user import User
from api.extensions import db
from datetime import datetime

class CollaborationService:
    """
    Service for collaboration features.
    """

    @staticmethod
    def add_comment(user_id, text, resource_type, resource_id, parent_id=None):
        """
        Add a comment to a resource.
        
        Args:
            user_id: ID of the user commenting.
            text: Comment text.
            resource_type: 'vulnerability' or 'ticket'.
            resource_id: ID of the resource.
            parent_id: Optional parent comment ID for threading.
            
        Returns:
            Created comment object.
        """
        comment = Comment(
            user_id=user_id,
            text=text,
            parent_id=parent_id
        )
        
        if resource_type == 'vulnerability':
            comment.vulnerability_instance_id = resource_id
        elif resource_type == 'ticket':
            comment.ticket_id = resource_id
        else:
            raise ValueError("Invalid resource type")
            
        db.session.add(comment)
        db.session.commit()
        
        # Log activity
        # (In a real app, we'd want to avoid circular imports or use signals)
        # For simplicity, we'll just create the log here if possible, or skip it.
        # Let's skip explicit activity logging here for now to keep it simple, 
        # or we can add it if ActivityLog is available.
        
        return comment

    @staticmethod
    def get_comments(resource_type, resource_id):
        """
        Get comments for a resource.
        """
        query = Comment.query.filter(Comment.parent_id == None) # Get top-level comments
        
        if resource_type == 'vulnerability':
            query = query.filter(Comment.vulnerability_instance_id == resource_id)
        elif resource_type == 'ticket':
            query = query.filter(Comment.ticket_id == resource_id)
            
        return query.order_by(Comment.created_at.desc()).all()

    @staticmethod
    def get_activity_feed(user_id, limit=20):
        """
        Get activity feed for a user (personal + team).
        """
        user = User.query.get(user_id)
        if not user:
            return []
            
        # Get user's teams
        team_ids = [t.id for t in user.teams]
        
        # This logic can be complex. For now, let's return:
        # 1. Activities by the user
        # 2. Activities by other members of the user's teams (optional)
        # 3. System activities relevant to the user
        
        # Simple version: All activities for now, or filtered by user/team if we had team_id on ActivityLog
        # Since ActivityLog doesn't have team_id yet, let's just return global activities 
        # or activities by users in the same teams.
        
        # Get IDs of all users in my teams
        teammate_ids = set()
        for team in user.teams:
            for member in team.members:
                teammate_ids.add(member.id)
        
        # Include self
        teammate_ids.add(user_id)
        
        activities = ActivityLog.query.filter(
            ActivityLog.user_id.in_(teammate_ids)
        ).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
        
        return activities
