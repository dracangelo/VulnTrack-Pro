import os
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationService:
    @staticmethod
    def send_notification(user_id, message, subject="VulnTrack Notification"):
        """
        Send notification via configured channels (Email, Slack).
        """
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
    def notify_ticket_assignment(ticket, user_id):
        subject = f"Ticket Assigned: #{ticket.id}"
        message = f"You have been assigned to ticket #{ticket.id}: {ticket.title}\nPriority: {ticket.priority}\nStatus: {ticket.status}"
        NotificationService.send_notification(user_id, message, subject)
