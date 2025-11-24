from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.target import Target

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

@target_bp.route('/<int:id>', methods=['DELETE'])
def delete_target(id):
    target = Target.query.get_or_404(id)
    db.session.delete(target)
    db.session.commit()
    return jsonify({'message': 'Target deleted'})
