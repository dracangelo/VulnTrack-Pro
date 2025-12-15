from run import app
from api.extensions import db
from api.models.user import User
from api.models.role import Role
from api.models.target import Target
from api.models.scan import Scan
from werkzeug.security import generate_password_hash
import time

def test_in_memory():
    print("Testing with in-memory database...")
    
    # Override config to use memory DB
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        # 1. Create Tables
        print("Creating tables...")
        db.create_all()
        
        # 2. Create Roles & Admin
        print("Creating admin...")
        if not Role.query.filter_by(name='admin').first():
            admin_role = Role(name='admin', description='Administrator')
            db.session.add(admin_role)
        else:
            admin_role = Role.query.filter_by(name='admin').first()
            
        db.session.commit()
        
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@vulntrack.local',
                password_hash=generate_password_hash('admin'),
                role=admin_role
            )
            db.session.add(admin)
            db.session.commit()
        else:
            admin = User.query.filter_by(username='admin').first()
        
        # 3. Create Target
        print("Creating target...")
        if not Target.query.filter_by(name='ScanTestTarget').first():
            target = Target(name='ScanTestTarget', ip_address='127.0.0.1', user_id=admin.id)
            db.session.add(target)
            db.session.commit()
        else:
            target = Target.query.filter_by(name='ScanTestTarget').first()
        
        # 4. Start Scan
        print("Starting scan...")
        scan_manager = app.scan_manager
        scan_id = scan_manager.start_scan(
            target_id=target.id,
            scan_type='nmap_quick',
            user_id=admin.id
        )
        print(f"Scan started with ID: {scan_id}")
        
        # 5. Monitor
        print("Monitoring scan status...")
        for i in range(10):
            db.session.expire_all()
            scan = Scan.query.get(scan_id)
            print(f"[{i}s] Scan Status: {scan.status}, Step: {scan.current_step}, Progress: {scan.progress}%")
            
            if scan.status in ['completed', 'failed', 'cancelled']:
                break
            time.sleep(1)
            
        if scan.status != 'completed':
            print("Scan did not complete in time.")
            print(f"Final Status: {scan.status}")
            print(f"Raw Output: {scan.raw_output}")
        else:
            print("Scan completed successfully!")

if __name__ == '__main__':
    test_in_memory()
