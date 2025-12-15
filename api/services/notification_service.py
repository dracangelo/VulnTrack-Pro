import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    @staticmethod
    def send_notification(user_id, message, subject="VulnTrack Notification", link=None, type='system'):
        """
        Send notification via configured channels (Email, Slack) and save to DB.
        """
        # 0. Save to Database
        try:
            NotificationService.create_notification(user_id, message, type, link)
        except Exception as e:
            print(f"Failed to create notification record: {e}")

        # 1. Log to console (always)
        print(f"[NOTIFICATION] User {user_id}: {message}")
        
        # 2. Send Email (if configured)
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        sender_email = os.getenv('SENDER_EMAIL')
        recipient_email = "user@example.com" # In real app, fetch from User model
        
        if smtp_server and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                
                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                print(f"Email sent to {recipient_email}")
            except Exception as e:
                print(f"Failed to send email: {e}")

        # 3. Send Slack Webhook (if configured)
        slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        if slack_webhook:
            try:
                payload = {"text": f"*{subject}*\n{message}"}
                requests.post(slack_webhook, json=payload)
                print("Slack notification sent")
            except Exception as e:
                print(f"Failed to send Slack notification: {e}")

    @staticmethod
    def create_notification(user_id, message, type='system', link=None):
        """
        Create a notification record in the database.
        """
        from api.models.notification import Notification
        from api.extensions import db
        
        notification = Notification(
            user_id=user_id,
            message=message,
            type=type,
            link=link
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def notify_ticket_assignment(ticket, user_id):
        subject = f"Ticket Assigned: #{ticket.id}"
        message = f"You have been assigned to ticket #{ticket.id}: {ticket.title}\nPriority: {ticket.priority}\nStatus: {ticket.status}"
        NotificationService.send_notification(user_id, message, subject, type='assignment', link=f"/tickets/{ticket.id}")

    @staticmethod
    def send_invite_email(email, token, role_name):
        """Send invitation email with token link"""
        subject = "Invitation to Join VulnTrack"
        # In a real app, this would be a proper URL to the frontend
        # For now, we'll assume the frontend is served at the root
        invite_link = f"http://localhost:5000/?invite_token={token}"
        
        message = f"""You have been invited to join VulnTrack as a {role_name}.
        
Please click the link below to register:
{invite_link}

This link will expire in 24 hours.
"""
        
        # We can reuse the email sending logic from send_notification, 
        # but send_notification expects a user_id. 
        # So we'll duplicate the SMTP part slightly or refactor.
        # For simplicity, let's just log it and try to send if SMTP is configured.
        
        print(f"[INVITE] Sending invite to {email} with token {token}")
        
        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        smtp_user = os.getenv('SMTP_USER')
        smtp_pass = os.getenv('SMTP_PASS')
        sender_email = os.getenv('SENDER_EMAIL')
        
        if smtp_server and smtp_user and smtp_pass:
            try:
                msg = MIMEMultipart()
                msg['From'] = sender_email
                msg['To'] = email
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))
                
                with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_pass)
                    server.send_message(msg)
                print(f"Invite email sent to {email}")
                return True
            except Exception as e:
                print(f"Failed to send invite email: {e}")
                return False
        return True # Return true if no SMTP (dev mode)
