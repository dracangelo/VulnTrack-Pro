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
        
        # Handle Mentions
        import re
        from api.models.user import User
        from api.models.vulnerability import VulnerabilityInstance
        from api.services.notification_service import NotificationService
        
        mentions = re.findall(r'@(\w+)', text)
        if mentions:
            mentioned_users = User.query.filter(User.username.in_(mentions)).all()
            for mentioned_user in mentioned_users:
                # 1. Send Notification
                # Determine link based on resource type
                link = None
                if resource_type == 'vulnerability':
                    link = f"/vulnerabilities/{resource_id}"
                elif resource_type == 'ticket':
                    link = f"/tickets/{resource_id}"
                
                commenter = User.query.get(user_id)
                commenter_name = commenter.username if commenter else "Unknown User"

                NotificationService.send_notification(
                    user_id=mentioned_user.id,
                    message=f"You were mentioned in a comment by {commenter_name}",
                    subject="You were mentioned",
                    type='mention',
                    link=link
                )
                
                # 2. Add to Vulnerability Assignees (if applicable)
                if resource_type == 'vulnerability':
                    vuln = VulnerabilityInstance.query.get(resource_id)
                    if vuln and mentioned_user not in vuln.assigned_users:
                        vuln.assigned_users.append(mentioned_user)
                        db.session.commit()
                        
                        # Notify about assignment as well? Maybe redundant if we notify about mention.
                        # Let's stick to just mention notification for now, but the assignment happens silently.
        
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

    @staticmethod
    def get_vulnerability_activity(vuln_id):
        """
        Get activity logs for a specific vulnerability instance.
        """
        return ActivityLog.query.filter_by(
            target_type='vulnerability_instance',
            target_id=vuln_id
        ).order_by(ActivityLog.timestamp.desc()).all()
