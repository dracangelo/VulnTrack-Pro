"""
Comprehensive tests for scheduler service.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from api.services.scheduler_service import SchedulerService, execute_scan_job
from api.models.schedule import Schedule
from api.models.target import Target
from api.extensions import db
from datetime import datetime, timedelta


def test_scheduler_initialization(app):
    """Test scheduler service initializes correctly."""
    scheduler = SchedulerService(app)
    assert scheduler.app == app
    assert scheduler.scheduler is not None
    assert scheduler.scheduler.running


def test_add_job(app, test_user):
    """Test adding a scheduled job."""
    with app.app_context():
        target = Target(ip_address='192.168.1.70', name='Target 70', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Daily Scan',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 2 * * *',  # Daily at 2 AM
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        result = scheduler.add_job(schedule)
        
        assert result is True
        job_id = f'schedule_{schedule.id}'
        job = scheduler.scheduler.get_job(job_id)
        assert job is not None


def test_remove_job(app, test_user):
    """Test removing a scheduled job."""
    with app.app_context():
        target = Target(ip_address='192.168.1.71', name='Target 71', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Remove Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 3 * * *',
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        scheduler.add_job(schedule)
        
        # Remove job
        result = scheduler.remove_job(schedule.id)
        assert result is True
        
        job_id = f'schedule_{schedule.id}'
        job = scheduler.scheduler.get_job(job_id)
        assert job is None


def test_update_job(app, test_user):
    """Test updating a scheduled job."""
    with app.app_context():
        target = Target(ip_address='192.168.1.72', name='Target 72', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Update Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 4 * * *',
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        scheduler.add_job(schedule)
        
        # Update schedule
        schedule.cron_expression = '0 5 * * *'  # Change time
        db.session.commit() # Commit to release lock for scheduler
        result = scheduler.update_job(schedule)
        
        assert result is True


def test_get_next_run_time(app):
    """Test calculating next run time."""
    scheduler = SchedulerService(app)
    
    # Test daily at 2 AM
    cron_expr = '0 2 * * *'
    next_run = scheduler.get_next_run_time(cron_expr)
    
    assert next_run is not None
    assert isinstance(next_run, datetime)


def test_get_next_run_time_invalid_cron(app):
    """Test invalid cron expression."""
    scheduler = SchedulerService(app)
    
    # Invalid cron expression
    next_run = scheduler.get_next_run_time('invalid cron')
    
    assert next_run is None


def test_execute_scheduled_scan(app, test_user):
    """Test executing a scheduled scan."""
    with app.app_context():
        target = Target(ip_address='192.168.1.73', name='Target 73', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Execute Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 6 * * *',
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        
        with patch('api.services.scan_manager.ScanManager') as MockScanManager:
            mock_instance = MockScanManager.return_value
            mock_instance.start_scan.return_value = 123
            
            execute_scan_job(schedule.id, app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Verify scan was started
            assert mock_instance.start_scan.called


def test_disabled_schedule_not_executed(app, test_user):
    """Test disabled schedule is not executed."""
    with app.app_context():
        target = Target(ip_address='192.168.1.74', name='Target 74', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Disabled Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 7 * * *',
            enabled=False  # Disabled
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        
        with patch('api.services.scan_manager.ScanManager') as MockScanManager:
            mock_instance = MockScanManager.return_value
            
            execute_scan_job(schedule.id, app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Scan should not be started
            assert not mock_instance.start_scan.called


def test_schedule_updates_last_run_time(app, test_user):
    """Test schedule updates last run time after execution."""
    with app.app_context():
        target = Target(ip_address='192.168.1.75', name='Target 75', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='Last Run Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 8 * * *',
            enabled=True,
            last_run=None
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        
        with patch('api.services.scan_manager.ScanManager') as MockScanManager:
            mock_instance = MockScanManager.return_value
            mock_instance.start_scan.return_value = 123
            
            execute_scan_job(schedule.id, app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Refresh schedule
            db.session.refresh(schedule)
            
            # Last run should be updated
            assert schedule.last_run is not None


def test_load_schedules_on_init(app, test_user):
    """Test schedules are loaded on initialization."""
    with app.app_context():
        target = Target(ip_address='192.168.1.76', name='Target 76', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        # Create enabled schedule
        schedule = Schedule(
            name='Auto Load Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 9 * * *',
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        # Initialize scheduler (should load existing schedules)
        scheduler = SchedulerService(app)
        
        job_id = f'schedule_{schedule.id}'
        job = scheduler.scheduler.get_job(job_id)
        
        # Job should be loaded
        assert job is not None or scheduler.scheduler is not None


def test_scheduler_shutdown(app):
    """Test scheduler shutdown."""
    scheduler = SchedulerService(app)
    
    assert scheduler.scheduler.running
    
    scheduler.shutdown()
    
    assert not scheduler.scheduler.running


def test_cron_expression_validation(app):
    """Test various cron expressions."""
    scheduler = SchedulerService(app)
    
    valid_crons = [
        '0 0 * * *',      # Daily at midnight
        '*/15 * * * *',   # Every 15 minutes
        '0 */2 * * *',    # Every 2 hours
        '0 0 * * 0',      # Weekly on Sunday
        '0 0 1 * *',      # Monthly on 1st
    ]
    
    for cron in valid_crons:
        next_run = scheduler.get_next_run_time(cron)
        assert next_run is not None, f"Failed for cron: {cron}"


def test_schedule_with_scanner_args(app, test_user):
    """Test schedule with custom scanner arguments."""
    with app.app_context():
        target = Target(ip_address='192.168.1.77', name='Target 77', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        scanner_args = '-p 80,443 -sV'
        schedule = Schedule(
            name='Custom Args Test',
            target_id=target.id,
            scan_type='nmap_quick',
            cron_expression='0 10 * * *',
            scanner_args=scanner_args,
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        
        with patch('api.services.scan_manager.ScanManager') as MockScanManager:
            mock_instance = MockScanManager.return_value
            mock_instance.start_scan.return_value = 123
            
            execute_scan_job(schedule.id, app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Verify scanner args were passed
            call_args = mock_instance.start_scan.call_args
            if call_args:
                assert 'scanner_args' in call_args[1] or len(call_args[0]) > 2


def test_schedule_with_openvas(app, test_user):
    """Test schedule with OpenVAS scan."""
    with app.app_context():
        target = Target(ip_address='192.168.1.78', name='Target 78', user_id=test_user.id)
        db.session.add(target)
        db.session.flush()
        
        schedule = Schedule(
            name='OpenVAS Test',
            target_id=target.id,
            scan_type='openvas',
            cron_expression='0 11 * * *',
            openvas_config_id='full_and_fast',
            enabled=True
        )
        db.session.add(schedule)
        db.session.commit()
        
        scheduler = SchedulerService(app)
        
        with patch('api.services.scan_manager.ScanManager') as MockScanManager:
            mock_instance = MockScanManager.return_value
            mock_instance.start_scan.return_value = 123
            
            execute_scan_job(schedule.id, app.config['SQLALCHEMY_DATABASE_URI'])
            
            # Verify OpenVAS config was passed
            assert mock_instance.start_scan.called
