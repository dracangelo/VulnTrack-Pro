from api.extensions import db
from api.models.role import Role, Permission, RolePermission
from api.models.user import User

class RBACService:
    """Role-Based Access Control service"""
    
    @staticmethod
    def initialize_default_roles():
        """Create default roles and permissions"""
        
        # Define permissions
        permissions_data = [
            # Targets
            ('targets:create', 'targets', 'create', 'Create new targets'),
            ('targets:read', 'targets', 'read', 'View targets'),
            ('targets:update', 'targets', 'update', 'Update targets'),
            ('targets:delete', 'targets', 'delete', 'Delete targets'),
            
            # Scans
            ('scans:create', 'scans', 'create', 'Create new scans'),
            ('scans:read', 'scans', 'read', 'View scans'),
            ('scans:update', 'scans', 'update', 'Update scans'),
            ('scans:delete', 'scans', 'delete', 'Delete scans'),
            
            # Vulnerabilities
            ('vulnerabilities:read', 'vulnerabilities', 'read', 'View vulnerabilities'),
            ('vulnerabilities:update', 'vulnerabilities', 'update', 'Update vulnerabilities'),
            
            # Tickets
            ('tickets:create', 'tickets', 'create', 'Create tickets'),
            ('tickets:read', 'tickets', 'read', 'View tickets'),
            ('tickets:update', 'tickets', 'update', 'Update tickets'),
            ('tickets:delete', 'tickets', 'delete', 'Delete tickets'),
            
            # Reports
            ('reports:create', 'reports', 'create', 'Create reports'),
            ('reports:read', 'reports', 'read', 'View reports'),
            ('reports:delete', 'reports', 'delete', 'Delete reports'),
            
            # Users
            ('users:create', 'users', 'create', 'Create users'),
            ('users:read', 'users', 'read', 'View users'),
            ('users:update', 'users', 'update', 'Update users'),
            ('users:delete', 'users', 'delete', 'Delete users'),
            
            # Roles
            ('roles:create', 'roles', 'create', 'Create roles'),
            ('roles:read', 'roles', 'read', 'View roles'),
            ('roles:update', 'roles', 'update', 'Update roles'),
            ('roles:delete', 'roles', 'delete', 'Delete roles'),
        ]
        
        # Create permissions
        for name, resource, action, description in permissions_data:
            existing = Permission.query.filter_by(name=name).first()
            if not existing:
                perm = Permission(
                    name=name,
                    resource=resource,
                    action=action,
                    description=description
                )
                db.session.add(perm)
        
        db.session.commit()
        
        # Define roles with permissions
        role_permissions = {
            'Admin': {
                'description': 'Full system access',
                'permissions': [p[0] for p in permissions_data]  # All permissions
            },
            'Manager': {
                'description': 'Manage scans, targets, vulnerabilities, and tickets',
                'permissions': [
                    'targets:create', 'targets:read', 'targets:update', 'targets:delete',
                    'scans:create', 'scans:read', 'scans:update', 'scans:delete',
                    'vulnerabilities:read', 'vulnerabilities:update',
                    'tickets:create', 'tickets:read', 'tickets:update', 'tickets:delete',
                    'reports:create', 'reports:read', 'reports:delete',
                    'users:read',
                ]
            },
            'Analyst': {
                'description': 'Analyze vulnerabilities and manage tickets',
                'permissions': [
                    'targets:read',
                    'scans:read',
                    'vulnerabilities:read', 'vulnerabilities:update',
                    'tickets:create', 'tickets:read', 'tickets:update',
                    'reports:create', 'reports:read',
                ]
            },
            'Viewer': {
                'description': 'Read-only access to all resources',
                'permissions': [
                    'targets:read',
                    'scans:read',
                    'vulnerabilities:read',
                    'tickets:read',
                    'reports:read',
                ]
            },
        }
        
        # Create roles and assign permissions
        for role_name, role_data in role_permissions.items():
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                role = Role(
                    name=role_name,
                    description=role_data['description'],
                    is_system=True
                )
                db.session.add(role)
                db.session.flush()
            
            # Clear existing permissions
            role.permissions = []
            
            # Assign permissions
            for perm_name in role_data['permissions']:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm and perm not in role.permissions:
                    role.permissions.append(perm)
        
        db.session.commit()
        print("✅ Default roles and permissions initialized")
    
    @staticmethod
    def check_permission(user, resource, action):
        """Check if user has permission"""
        if not user or not user.is_active:
            return False
        
        return user.has_permission(resource, action)
    
    @staticmethod
    def assign_role(user_id, role_id):
        """Assign role to user"""
        user = User.query.get(user_id)
        role = Role.query.get(role_id)
        
        if not user or not role:
            return False
        
        user.role_id = role_id
        db.session.commit()
        return True
    
    @staticmethod
    def get_all_roles():
        """Get all roles"""
        return Role.query.all()
    
    @staticmethod
    def get_all_permissions():
        """Get all permissions"""
        return Permission.query.all()
    
    @staticmethod
    def create_role(name, description, permission_ids):
        """Create new role with permissions"""
        if Role.query.filter_by(name=name).first():
            return None
        
        role = Role(name=name, description=description, is_system=False)
        
        # Assign permissions
        for perm_id in permission_ids:
            perm = Permission.query.get(perm_id)
            if perm:
                role.permissions.append(perm)
        
        db.session.add(role)
        db.session.commit()
        return role
    
    @staticmethod
    def update_role(role_id, name=None, description=None, permission_ids=None):
        """Update role"""
        role = Role.query.get(role_id)
        if not role or role.is_system:
            return None
        
        if name:
            role.name = name
        if description:
            role.description = description
        if permission_ids is not None:
            role.permissions = []
            for perm_id in permission_ids:
                perm = Permission.query.get(perm_id)
                if perm:
                    role.permissions.append(perm)
        
        db.session.commit()
        return role
    
    @staticmethod
    def delete_role(role_id):
        """Delete role (only non-system roles)"""
        role = Role.query.get(role_id)
        if not role or role.is_system:
            return False
        
        # Check if any users have this role
        if role.users:
            return False
        
        db.session.delete(role)
        db.session.commit()
        return True
