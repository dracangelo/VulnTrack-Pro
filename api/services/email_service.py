import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Service for sending emails.
    Currently implements a mock that logs to console/file.
    """
    
    @staticmethod
    def send_invitation_email(to_email, team_name, invite_link):
        """
        Send an invitation email.
        """
        subject = f"Invitation to join team {team_name} on VulnTrack"
        body = f"""
        Hello,
        
        You have been invited to join the team '{team_name}' on VulnTrack Pro.
        
        Click the link below to join:
        {invite_link}
        
        If you did not expect this invitation, please ignore this email.
        """
        
        # Mock sending
        logger.info(f"--- MOCK EMAIL START ---")
        logger.info(f"To: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body}")
        logger.info(f"--- MOCK EMAIL END ---")
        
        print(f"--- MOCK EMAIL SENT TO {to_email} ---")
        print(f"Link: {invite_link}")
        
        return True
