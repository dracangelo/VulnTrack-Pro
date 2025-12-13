import pytest
from unittest.mock import patch
from api import create_app
from api.extensions import db
from api.config import Config

class TestConfig(Config):
    TESTING = True
    # Use a file-based DB for tests to support multi-threading
    SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/test_vulntrack.db'
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"check_same_thread": False}}
    RATELIMIT_ENABLED = False # Disable rate limiting for tests

@pytest.fixture
def app():
    with patch('api.services.scheduler_service.SchedulerService') as MockScheduler:
        # Configure mock to do nothing
        mock_instance = MockScheduler.return_value
        mock_instance.start.return_value = None
        mock_instance.add_job.return_value = True
        
        app = create_app(TestConfig)
        
        with app.app_context():
            # Import models to ensure they are registered with SQLAlchemy
            import api.models
            db.create_all()
            yield app
            db.session.remove()
            import os
            if os.path.exists('/tmp/test_vulntrack.db'):
                os.remove('/tmp/test_vulntrack.db')


@pytest.fixture
def auth_header(app):
    from api.models.user import User
    from flask_jwt_extended import create_access_token
    from werkzeug.security import generate_password_hash
    
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.password_hash = generate_password_hash('password123')
        db.session.add(user)
        db.session.commit()
        
        token = create_access_token(identity=str(user.id))
        return {'Authorization': f'Bearer {token}'}

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
