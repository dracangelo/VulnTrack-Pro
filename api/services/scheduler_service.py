from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime
from api.extensions import db
from api.models.schedule import Schedule

class SchedulerService:
    """Service for managing scheduled scans using APScheduler"""
    
    def __init__(self, app=None):
        self.app = app
        self.scheduler = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize scheduler with Flask app"""
        self.app = app
        
        # Configure job store to use same database
        jobstores = {
            'default': SQLAlchemyJobStore(url=app.config['SQLALCHEMY_DATABASE_URI'])
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.scheduler.start()
        
        # Load existing schedules from database
        with app.app_context():
            self.load_schedules()
    
    def load_schedules(self):
        """Load all enabled schedules from database"""
        try:
            schedules = Schedule.query.filter_by(enabled=True).all()
            
            for schedule in schedules:
                self.add_job(schedule)
        except Exception as e:
            # Table might not exist yet during initial migration
            print(f"Could not load schedules: {e}")
    
    def add_job(self, schedule):
        """Add a scheduled job to APScheduler"""
        try:
            # Create cron trigger
            trigger = CronTrigger.from_crontab(schedule.cron_expression)
            
            # Add job
            job_id = f'schedule_{schedule.id}'
            
            # Remove existing job if it exists
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Add new job
            self.scheduler.add_job(
                func=self._execute_scheduled_scan,
                trigger=trigger,
                id=job_id,
                args=[schedule.id],
                replace_existing=True
            )
            
            # Update next run time
            job = self.scheduler.get_job(job_id)
            if job:
                schedule.next_run = job.next_run_time
                db.session.commit()
            
            return True
            
        except Exception as e:
            print(f"Error adding scheduled job: {e}")
            return False
    
    def remove_job(self, schedule_id):
        """Remove a scheduled job"""
        try:
            job_id = f'schedule_{schedule_id}'
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            return True
        except Exception as e:
            print(f"Error removing scheduled job: {e}")
            return False
    
    def update_job(self, schedule):
        """Update an existing scheduled job"""
        self.remove_job(schedule.id)
        if schedule.enabled:
            return self.add_job(schedule)
        return True
    
    def _execute_scheduled_scan(self, schedule_id):
        """Execute a scheduled scan"""
        with self.app.app_context():
            schedule = Schedule.query.get(schedule_id)
            
            if not schedule or not schedule.enabled:
                return
            
            # Import here to avoid circular imports
            from api.services.scan_manager import ScanManager
            
            # Create scan manager
            scan_manager = ScanManager(self.app)
            
            # Start scan
            try:
                scan_id = scan_manager.start_scan(
                    target_id=schedule.target_id,
                    scan_type=schedule.scan_type,
                    scanner_args=schedule.scanner_args,
                    openvas_config_id=schedule.openvas_config_id
                )
                
                # Update last run time
                schedule.last_run = datetime.utcnow()
                
                # Update next run time
                job_id = f'schedule_{schedule_id}'
                job = self.scheduler.get_job(job_id)
                if job:
                    schedule.next_run = job.next_run_time
                
                db.session.commit()
                
                print(f"Scheduled scan started: {scan_id} for schedule {schedule_id}")
                
            except Exception as e:
                print(f"Error executing scheduled scan: {e}")
    
    def get_next_run_time(self, cron_expression):
        """Calculate next run time for a cron expression"""
        try:
            trigger = CronTrigger.from_crontab(cron_expression)
            next_run = trigger.get_next_fire_time(None, datetime.now())
            return next_run
        except Exception as e:
            print(f"Error calculating next run time: {e}")
            return None
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
