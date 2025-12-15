from run import app
from api.extensions import db
from api.models.scan import Scan
from api.models.target import Target
from api.models.user import User
import time
import sys

def reproduce_scan():
    print("Starting reproduction script...")
    
    with app.app_context():
        # 1. Get Admin User
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Admin user not found. Run reset_db.py first.")
            return

        # 2. Create Target
        target = Target(name='ScanTestTarget', ip_address='127.0.0.1', user_id=admin.id)
        db.session.add(target)
        db.session.commit()
        print(f"Created target: {target.name} (ID: {target.id})")

        # 3. Start Scan via ScanManager
        print("Starting scan...")
        from api.services.scan_manager import ScanManager
        # We need to access the singleton scan_manager from the app
        # But app.scan_manager is initialized in create_app.
        # Since we imported 'app' from 'run', it should be there.
        
        scan_manager = app.scan_manager
        
        scan_id = scan_manager.start_scan(
            target_id=target.id,
            scan_type='nmap_quick',
            user_id=admin.id
        )
        print(f"Scan started with ID: {scan_id}")

        # 4. Monitor Scan Status
        print("Monitoring scan status...")
        for i in range(60):
            db.session.expire_all() # Refresh objects
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
    reproduce_scan()
