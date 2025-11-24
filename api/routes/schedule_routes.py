from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.schedule import Schedule
from api.models.target import Target
from datetime import datetime

schedule_bp = Blueprint('schedules', __name__, url_prefix='/api/schedules')

@schedule_bp.route('/', methods=['GET'])
def get_schedules():
    """Get all schedules"""
    schedules = Schedule.query.order_by(Schedule.created_at.desc()).all()
    return jsonify([s.to_dict() for s in schedules]), 200

@schedule_bp.route('/<int:schedule_id>', methods=['GET'])
def get_schedule(schedule_id):
    """Get a specific schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    return jsonify(schedule.to_dict()), 200

@schedule_bp.route('/', methods=['POST'])
def create_schedule():
    """Create a new schedule"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['name', 'target_id', 'scan_type', 'cron_expression']
    for field in required_fields:
        if field not in data:
            return jsonify({'error': f'Missing required field: {field}'}), 400
    
    # Verify target exists
    target = Target.query.get(data['target_id'])
    if not target:
        return jsonify({'error': 'Target not found'}), 404
    
    # Validate cron expression and calculate next run
    from flask import current_app
    scheduler_service = current_app.scheduler_service
    next_run = scheduler_service.get_next_run_time(data['cron_expression'])
    
    if not next_run:
        return jsonify({'error': 'Invalid cron expression'}), 400
    
    # Create schedule
    schedule = Schedule(
        name=data['name'],
        description=data.get('description', ''),
        target_id=data['target_id'],
        scan_type=data['scan_type'],
        scanner_args=data.get('scanner_args'),
        openvas_config_id=data.get('openvas_config_id'),
        cron_expression=data['cron_expression'],
        next_run=next_run,
        enabled=data.get('enabled', True)
    )
    
    db.session.add(schedule)
    db.session.commit()
    
    # Add to scheduler if enabled
    if schedule.enabled:
        scheduler_service.add_job(schedule)
    
    return jsonify(schedule.to_dict()), 201

@schedule_bp.route('/<int:schedule_id>', methods=['PUT'])
def update_schedule(schedule_id):
    """Update a schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    data = request.get_json()
    
    # Update fields
    if 'name' in data:
        schedule.name = data['name']
    if 'description' in data:
        schedule.description = data['description']
    if 'target_id' in data:
        target = Target.query.get(data['target_id'])
        if not target:
            return jsonify({'error': 'Target not found'}), 404
        schedule.target_id = data['target_id']
    if 'scan_type' in data:
        schedule.scan_type = data['scan_type']
    if 'scanner_args' in data:
        schedule.scanner_args = data['scanner_args']
    if 'openvas_config_id' in data:
        schedule.openvas_config_id = data['openvas_config_id']
    
    # Update cron expression
    if 'cron_expression' in data:
        from flask import current_app
        scheduler_service = current_app.scheduler_service
        next_run = scheduler_service.get_next_run_time(data['cron_expression'])
        
        if not next_run:
            return jsonify({'error': 'Invalid cron expression'}), 400
        
        schedule.cron_expression = data['cron_expression']
        schedule.next_run = next_run
    
    # Update enabled status
    if 'enabled' in data:
        schedule.enabled = data['enabled']
    
    schedule.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Update scheduler
    from flask import current_app
    current_app.scheduler_service.update_job(schedule)
    
    return jsonify(schedule.to_dict()), 200

@schedule_bp.route('/<int:schedule_id>', methods=['DELETE'])
def delete_schedule(schedule_id):
    """Delete a schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    
    # Remove from scheduler
    from flask import current_app
    current_app.scheduler_service.remove_job(schedule_id)
    
    db.session.delete(schedule)
    db.session.commit()
    
    return jsonify({'message': 'Schedule deleted'}), 200

@schedule_bp.route('/<int:schedule_id>/toggle', methods=['POST'])
def toggle_schedule(schedule_id):
    """Enable or disable a schedule"""
    schedule = Schedule.query.get_or_404(schedule_id)
    
    schedule.enabled = not schedule.enabled
    schedule.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Update scheduler
    from flask import current_app
    current_app.scheduler_service.update_job(schedule)
    
    return jsonify(schedule.to_dict()), 200

@schedule_bp.route('/validate-cron', methods=['POST'])
def validate_cron():
    """Validate a cron expression and return next run time"""
    data = request.get_json()
    
    if 'cron_expression' not in data:
        return jsonify({'error': 'Missing cron_expression'}), 400
    
    from flask import current_app
    scheduler_service = current_app.scheduler_service
    next_run = scheduler_service.get_next_run_time(data['cron_expression'])
    
    if not next_run:
        return jsonify({'valid': False, 'error': 'Invalid cron expression'}), 200
    
    return jsonify({
        'valid': True,
        'next_run': next_run.isoformat(),
        'next_run_human': next_run.strftime('%Y-%m-%d %H:%M:%S')
    }), 200
