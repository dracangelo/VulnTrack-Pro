from flask import Blueprint, jsonify, request
from api.extensions import db
from api.models.target import TargetGroup

target_group_bp = Blueprint('target_groups', __name__, url_prefix='/api/target-groups')

@target_group_bp.route('/', methods=['GET'])
def get_groups():
    groups = TargetGroup.query.all()
    return jsonify([{'id': g.id, 'name': g.name, 'description': g.description} for g in groups])

@target_group_bp.route('/<int:id>', methods=['GET'])
def get_group(id):
    group = TargetGroup.query.get_or_404(id)
    return jsonify({'id': group.id, 'name': group.name, 'description': group.description})

@target_group_bp.route('/', methods=['POST'])
def create_group():
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Invalid data'}), 400
    
    new_group = TargetGroup(name=data['name'], description=data.get('description'))
    db.session.add(new_group)
    db.session.commit()
    
    return jsonify({'message': 'Target Group created', 'id': new_group.id}), 201

@target_group_bp.route('/<int:id>', methods=['PUT'])
def update_group(id):
    group = TargetGroup.query.get_or_404(id)
    data = request.get_json()
    
    group.name = data.get('name', group.name)
    group.description = data.get('description', group.description)
    
    db.session.commit()
    return jsonify({'message': 'Target Group updated'})

@target_group_bp.route('/<int:id>', methods=['DELETE'])
def delete_group(id):
    group = TargetGroup.query.get_or_404(id)
    db.session.delete(group)
    db.session.commit()
    return jsonify({'message': 'Target Group deleted'})
