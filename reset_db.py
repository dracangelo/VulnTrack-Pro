from run import app
from api.extensions import db
from api.models.user import User
from api.models.role import Role
from werkzeug.security import generate_password_hash
import os

def reset_db():
    print("Resetting database...")
    print(f"DB URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    # Delete database file if exists
    db_path = 'vulntrack.db'
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Deleted existing database file.")
    
    with app.app_context():
        # Create all tables defined in models
        print("Creating tables from models...")
        db.create_all()
        
        # Create roles
        print("Creating roles...")
        if not Role.query.filter_by(name='admin').first():
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
        else:
            admin_role = Role.query.filter_by(name='admin').first()
            
        if not Role.query.filter_by(name='user').first():
            user_role = Role(name='user', description='Regular User')
            db.session.add(user_role)
        
        db.session.commit()

        # Create admin user
        print("Creating admin user...")
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@vulntrack.local',
                password_hash=generate_password_hash('admin'),
                role=admin_role
            )
            db.session.add(admin)
            db.session.commit()
        print("Database reset complete. Admin user created.")

if __name__ == '__main__':
    reset_db()
