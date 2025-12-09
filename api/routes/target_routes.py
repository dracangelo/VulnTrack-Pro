from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.target import Target
from api.utils.target_utils import (
    validate_cidr, expand_cidr, 
    validate_hostname, resolve_hostname,
    validate_ip_address
)

target_bp = Blueprint('targets', __name__, url_prefix='/api/targets')

@target_bp.route('/', methods=['GET'])
def get_targets():
    targets = Target.query.all()
    return jsonify([{'id': t.id, 'name': t.name, 'ip_address': t.ip_address, 'description': t.description, 'group_id': t.group_id} for t in targets])

@target_bp.route('/<int:id>', methods=['GET'])
def get_target(id):
    target = Target.query.get_or_404(id)
    return jsonify({'id': target.id, 'name': target.name, 'ip_address': target.ip_address, 'description': target.description, 'group_id': target.group_id})

@target_bp.route('/', methods=['POST'])
def create_target():
    data = request.get_json()
    if not data or 'name' not in data or 'ip_address' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    new_target = Target(name=data['name'], ip_address=data['ip_address'], description=data.get('description'), group_id=data.get('group_id'))
    db.session.add(new_target)
    db.session.commit()
    
    return jsonify({'message': 'Target created', 'id': new_target.id}), 201

@target_bp.route('/bulk', methods=['POST'])
def create_bulk_targets():
    """
    Create multiple targets from CIDR range, hostname, or single IP.
    
    Expected JSON:
    {
        "input": "192.168.1.0/24" or "example.com" or "192.168.1.1",
        "type": "cidr" or "hostname" or "ip",
        "description": "Optional description",
        "group_id": Optional group ID
    }
    """
    data = request.get_json()
    
    if not data or 'input' not in data or 'type' not in data:
        return jsonify({'error': 'Missing required fields: input and type'}), 400
    
    input_value = data['input'].strip()
    input_type = data['type'].lower()
    description = data.get('description', '')
    group_id = data.get('group_id')
    
    created_targets = []
    errors = []
    
    try:
        if input_type == 'cidr':
            # Validate and expand CIDR
            if not validate_cidr(input_value):
                return jsonify({'error': f'Invalid CIDR notation: {input_value}'}), 400
            
            # Check if user wants to keep as single target
            keep_as_single = data.get('keep_as_single', False)
            
            if keep_as_single:
                # Create single target with CIDR notation
                existing = Target.query.filter_by(ip_address=input_value).first()
                if existing:
                    return jsonify({'error': f'Target with CIDR {input_value} already exists (ID: {existing.id})'}), 409
                
                target = Target(
                    name=data.get('name', input_value),
                    ip_address=input_value,
                    description=description or f'CIDR range: {input_value}',
                    group_id=group_id
                )
                db.session.add(target)
                db.session.commit()
                
                return jsonify({
                    'message': 'CIDR target created',
                    'id': target.id,
                    'cidr': input_value
                }), 201
            else:
                # Expand CIDR to individual IPs
                ip_addresses = expand_cidr(input_value)
                
                # Limit to prevent abuse (max 1024 IPs)
                if len(ip_addresses) > 1024:
                    return jsonify({'error': f'CIDR range too large. Maximum 1024 IPs allowed. This range contains {len(ip_addresses)} IPs.'}), 400
                
                # Create targets for each IP
                for ip in ip_addresses:
                    # Check if target already exists
                    existing = Target.query.filter_by(ip_address=ip).first()
                    if existing:
                        errors.append(f'{ip} already exists')
                        continue
                    
                    target = Target(
                        name=f'{input_value} - {ip}',
                        ip_address=ip,
                        description=description or f'Auto-created from CIDR: {input_value}',
                        group_id=group_id
                    )
                    db.session.add(target)
                    created_targets.append(ip)
                
                db.session.commit()
                
                return jsonify({
                    'message': f'Created {len(created_targets)} targets from CIDR range',
                    'created': len(created_targets),
                    'errors': errors,
                    'targets': created_targets
                }), 201
            
        elif input_type == 'hostname':
            # Validate hostname
            if not validate_hostname(input_value):
                return jsonify({'error': f'Invalid hostname: {input_value}'}), 400
            
            # Resolve hostname to IP
            try:
                ip_address = resolve_hostname(input_value)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400
            
            # Check if target already exists
            existing = Target.query.filter_by(ip_address=ip_address).first()
            if existing:
                return jsonify({'error': f'Target with IP {ip_address} already exists (ID: {existing.id})'}), 409
            
            # Create target
            target = Target(
                name=input_value,
                ip_address=ip_address,
                description=description or f'Resolved from hostname: {input_value}',
                group_id=group_id
            )
            db.session.add(target)
            db.session.commit()
            
            return jsonify({
                'message': 'Target created from hostname',
                'id': target.id,
                'hostname': input_value,
                'ip_address': ip_address
            }), 201
            
        elif input_type == 'ip':
            # Validate IP address
            if not validate_ip_address(input_value):
                return jsonify({'error': f'Invalid IP address: {input_value}'}), 400
            
            # Check if target already exists
            existing = Target.query.filter_by(ip_address=input_value).first()
            if existing:
                return jsonify({'error': f'Target with IP {input_value} already exists (ID: {existing.id})'}), 409
            
            # Create target
            target = Target(
                name=data.get('name', input_value),
                ip_address=input_value,
                description=description,
                group_id=group_id
            )
            db.session.add(target)
            db.session.commit()
            
            return jsonify({
                'message': 'Target created',
                'id': target.id
            }), 201
            
        else:
            return jsonify({'error': f'Invalid type: {input_type}. Must be "cidr", "hostname", or "ip"'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error creating targets: {str(e)}'}), 500

@target_bp.route('/<int:id>', methods=['PUT'])
def update_target(id):
    target = Target.query.get_or_404(id)
    data = request.get_json()
    
    target.name = data.get('name', target.name)
    target.ip_address = data.get('ip_address', target.ip_address)
    target.description = data.get('description', target.description)
    target.group_id = data.get('group_id', target.group_id)
    
    db.session.commit()
    return jsonify({'message': 'Target updated'})

@target_bp.route('/<int:target_id>', methods=['DELETE'])
def delete_target(target_id):
    target = Target.query.get_or_404(target_id)
    db.session.delete(target)
    db.session.commit()
    return jsonify({'message': 'Target deleted successfully'})

# Bulk Operations
from api.services.bulk_service import BulkService

@target_bp.route('/bulk/scan', methods=['POST'])
def bulk_scan_targets():
    data = request.get_json()
    target_ids = data.get('target_ids', [])
    scan_type = data.get('scan_type', 'quick')
    
    if not target_ids:
        return jsonify({'error': 'No target IDs provided'}), 400
        
    scan_ids = BulkService.bulk_scan_targets(target_ids, scan_type)
    return jsonify({'message': f'Started {len(scan_ids)} scans', 'scan_ids': scan_ids}), 200

@target_bp.route('/bulk/group', methods=['POST'])
def bulk_assign_group():
    data = request.get_json()
    target_ids = data.get('target_ids', [])
    group_id = data.get('group_id')
    
    if not target_ids or not group_id:
        return jsonify({'error': 'Missing target_ids or group_id'}), 400
        
    count = BulkService.bulk_assign_group(target_ids, group_id)
    return jsonify({'message': f'Updated {count} targets'}), 200

@target_bp.route('/bulk/delete', methods=['POST'])
def bulk_delete_targets():
    data = request.get_json()
    target_ids = data.get('target_ids', [])
    
    if not target_ids:
        return jsonify({'error': 'No target IDs provided'}), 400
        
    count = BulkService.bulk_delete_targets(target_ids)
    return jsonify({'message': f'Deleted {count} targets'}), 200

@target_bp.route('/bulk/edit', methods=['POST'])
def bulk_edit_targets():
    data = request.get_json()
    target_ids = data.get('target_ids', [])
    update_data = data.get('data', {})
    
    if not target_ids or not update_data:
        return jsonify({'error': 'Missing target_ids or update data'}), 400
        
    count = BulkService.bulk_edit_targets(target_ids, update_data)
    return jsonify({'message': f'Updated {count} targets'}), 200



