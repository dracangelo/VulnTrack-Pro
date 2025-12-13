from run import app
from api.extensions import db
from api.models.user import User
from api.models.role import Role
from werkzeug.security import generate_password_hash

with app.app_context():
    # Create roles
    admin_role = Role(name='admin', description='Administrator')
    user_role = Role(name='user', description='Regular User')
    db.session.add(admin_role)
    db.session.add(user_role)
    db.session.commit()

    # Create admin user
    admin = User(
        username='admin',
        email='admin@vulntrack.local',
        password_hash=generate_password_hash('admin'),
        role=admin_role
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin user created.")
