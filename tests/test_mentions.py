import pytest
from api.models.user import User
from api.models.vulnerability import VulnerabilityInstance, Vulnerability
from api.models.notification import Notification
from api.models.comment import Comment
from api.services.collaboration_service import CollaborationService
from api.extensions import db

@pytest.fixture
def test_users(app):
    with app.app_context():
        user1 = User(username='user1', email='user1@example.com')
        user2 = User(username='user2', email='user2@example.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        return user1, user2

@pytest.fixture
def test_vuln(app, test_users):
    with app.app_context():
        # Create dependencies for VulnerabilityInstance
        # Assuming Scan and Target exist or we need to mock/create them.
        # For simplicity, let's try to create minimal required objects if possible, 
        # or rely on existing fixtures if available.
        # Since we don't have easy access to other fixtures here without importing them,
        # let's try to mock the DB interaction or create minimal objects.
        
        # Actually, let's just use the service directly and mock the DB objects if needed,
        # or better, rely on integration test style if we can set up the DB.
        pass

# We will use a more integration-test style approach using the client or app context
# assuming the DB is set up by conftest.

def test_mention_creates_notification(client, app):
    """Test that mentioning a user creates a notification."""
    with app.app_context():
        # Setup
        user1 = User(username='commenter', email='commenter@example.com')
        user2 = User(username='mentioned', email='mentioned@example.com')
        db.session.add(user1)
        db.session.add(user2)
        db.session.commit()
        
        # Create a dummy vulnerability instance
        # We need Scan and Target first.
        from api.models.scan import Scan
        from api.models.target import Target
        
        target = Target(name='test_target', ip_address='127.0.0.1')
        scan = Scan(target=target, scan_type='nmap_quick')
        db.session.add(target)
        db.session.add(scan)
        db.session.commit()
        
        vuln_def = Vulnerability(name='Test Vuln', severity='High')
        db.session.add(vuln_def)
        db.session.commit()
        
        vuln_instance = VulnerabilityInstance(
            vulnerability_id=vuln_def.id,
            scan_id=scan.id,
            target_id=target.id
        )
        db.session.add(vuln_instance)
        db.session.commit()
        
        # Action: User1 comments mentioning User2
        CollaborationService.add_comment(
            user_id=user1.id,
            text="Hey @mentioned, check this out!",
            resource_type='vulnerability',
            resource_id=vuln_instance.id
        )
        
        # Assertion: Notification created for User2
        notification = Notification.query.filter_by(user_id=user2.id).first()
        assert notification is not None
        assert notification.type == 'mention'
        assert "mentioned in a comment" in notification.message
        assert notification.link == f"/vulnerabilities/{vuln_instance.id}"
        
        # Assertion: User2 assigned to Vulnerability
        vuln_instance = VulnerabilityInstance.query.get(vuln_instance.id)
        assert user2 in vuln_instance.assigned_users

def test_multiple_mentions(client, app):
    """Test multiple mentions in one comment."""
    with app.app_context():
        u1 = User(username='u1', email='u1@example.com')
        u2 = User(username='u2', email='u2@example.com')
        u3 = User(username='u3', email='u3@example.com')
        db.session.add_all([u1, u2, u3])
        db.session.commit()
        
        # Create dummy resource (Ticket for variety)
        from api.models.ticket import Ticket
        ticket = Ticket(title="Test Ticket", description="Desc", status="open", priority="high")
        db.session.add(ticket)
        db.session.commit()
        
        CollaborationService.add_comment(
            user_id=u1.id,
            text="Hello @u2 and @u3",
            resource_type='ticket',
            resource_id=ticket.id
        )
        
        n2 = Notification.query.filter_by(user_id=u2.id).first()
        n3 = Notification.query.filter_by(user_id=u3.id).first()
        
        assert n2 is not None
        assert n3 is not None
        assert n2.link == f"/tickets/{ticket.id}"

def test_invalid_mention_ignored(client, app):
    """Test that mentioning non-existent user does nothing."""
    with app.app_context():
        u1 = User(username='sender', email='sender@example.com')
        db.session.add(u1)
        db.session.commit()
        
        # Create dummy ticket
        from api.models.ticket import Ticket
        ticket = Ticket(title="Test Ticket 2", description="Desc", status="open", priority="high")
        db.session.add(ticket)
        db.session.commit()
        
        CollaborationService.add_comment(
            user_id=u1.id,
            text="Hello @nobody",
            resource_type='ticket',
            resource_id=ticket.id
        )
        
        # Should be no notifications
        assert Notification.query.count() == 0
