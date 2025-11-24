class NotificationService:
    @staticmethod
    def send_notification(user_id, message):
        # In a real app, this would send an email or push notification
        # For now, we'll just print to console
        print(f"NOTIFICATION for User {user_id}: {message}")

    @staticmethod
    def notify_ticket_assignment(ticket, user_id):
        message = f"You have been assigned to ticket #{ticket.id}: {ticket.title}"
        NotificationService.send_notification(user_id, message)
