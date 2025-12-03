from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from api.services.rbac_service import RBACService
from api.models.role import Role, Permission
from api.models.user import User
from api.utils.decorators import require_permission, require_role
from api.extensions import db

role_bp = Blueprint('roles', __name__, url_prefix='/api/roles')

@role_bp.route('/', methods=['GET'])
@jwt_required()
@require_permission('roles', 'read')
def get_roles():
    """Get all roles"""
    roles = RBACService.get_all_roles()
    return jsonify({'roles': [r.to_dict() for r in roles]})

@role_bp.route('/<int:role_id>', methods=['GET'])
@jwt_required()
@require_permission('roles', 'read')
def get_role(role_id):
    """Get specific role"""
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Role not found'}), 404
    
    return jsonify(role.to_dict())

@role_bp.route('/', methods=['POST'])
@jwt_required()
@require_permission('roles', 'create')
def create_role():
    """Create new role"""
    data = request.get_json()
    
    name = data.get('name')
    description = data.get('description', '')
    permission_ids = data.get('permission_ids', [])
    
    if not name:
        return jsonify({'error': 'Role name is required'}), 400
    
    role = RBACService.create_role(name, description, permission_ids)
    
    if not role:
        return jsonify({'error': 'Role already exists'}), 400
    
    return jsonify(role.to_dict()), 201

@role_bp.route('/<int:role_id>', methods=['PUT'])
@jwt_required()
@require_permission('roles', 'update')
def update_role(role_id):
    """Update role"""
    data = request.get_json()
    
    role = RBACService.update_role(
        role_id,
        name=data.get('name'),
        description=data.get('description'),
        permission_ids=data.get('permission_ids')
    )
    
    if not role:
        return jsonify({'error': 'Role not found or is system role'}), 400
    
    return jsonify(role.to_dict())

@role_bp.route('/<int:role_id>', methods=['DELETE'])
@jwt_required()
@require_permission('roles', 'delete')
def delete_role(role_id):
    """Delete role"""
    if RBACService.delete_role(role_id):
        return jsonify({'message': 'Role deleted successfully'})
    else:
        return jsonify({'error': 'Cannot delete system role or role with users'}), 400

@role_bp.route('/permissions', methods=['GET'])
@jwt_required()
@require_permission('roles', 'read')
def get_permissions():
    """Get all permissions"""
    permissions = RBACService.get_all_permissions()
    return jsonify({'permissions': [p.to_dict() for p in permissions]})

@role_bp.route('/assign', methods=['POST'])
@jwt_required()
@require_permission('users', 'update')
def assign_role_to_user():
    """Assign role to user"""
    data = request.get_json()
    
    user_id = data.get('user_id')
    role_id = data.get('role_id')
    
    if not user_id or not role_id:
        return jsonify({'error': 'user_id and role_id are required'}), 400
    
    if RBACService.assign_role(user_id, role_id):
        return jsonify({'message': 'Role assigned successfully'})
    else:
        return jsonify({'error': 'User or role not found'}), 404

@role_bp.route('/initialize', methods=['POST'])
@jwt_required()
@require_role('Admin')
def initialize_roles():
    """Initialize default roles and permissions (Admin only)"""
    try:
        RBACService.initialize_default_roles()
        return jsonify({'message': 'Default roles and permissions initialized'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
