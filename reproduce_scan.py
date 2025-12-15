import time
import threading
from api import create_app
from api.extensions import db
from api.models.target import Target
from api.models.scan import Scan
from api.services.scan_manager import ScanManager

def reproduce_scan_issue():
    app = create_app()
    with app.app_context():
        # Ensure we have a user (admin created in previous step)
        from api.models.user import User
        user = User.query.filter_by(username='admin').first()
        if not user:
            print("Error: Admin user not found. Did you run create_admin.py?")
            return

        # Create a target
        target = Target(
            name='Localhost Test',
            ip_address='127.0.0.1',
            description='Test Target',
            user_id=user.id
        )
        db.session.add(target)
        db.session.commit()
        print(f"Created target: {target.id}")

        # Initialize ScanManager
        scan_manager = ScanManager(app)
        
        # Start a scan
        print("Starting scan...")
        scan_id = scan_manager.start_scan(
            target_id=target.id,
            scan_type='nmap',
            scanner_args='-F', # Fast scan
            user_id=user.id
        )
        print(f"Scan started with ID: {scan_id}")

        # Monitor scan status
        for _ in range(20): # Wait up to 20 seconds
            scan = Scan.query.get(scan_id)
            print(f"Scan Status: {scan.status}, Progress: {scan.progress}, Step: {scan.current_step}")
            
            if scan.status in ['completed', 'failed', 'cancelled']:
                break
            
            time.sleep(1)
            db.session.refresh(scan)

        print(f"Final Scan Status: {scan.status}")
        if scan.status != 'completed':
            print("ISSUE REPRODUCED: Scan did not complete successfully.")
            if scan.raw_output:
                print(f"Raw Output: {scan.raw_output}")
        else:
            print("Scan completed successfully.")

if __name__ == '__main__':
    reproduce_scan_issue()
