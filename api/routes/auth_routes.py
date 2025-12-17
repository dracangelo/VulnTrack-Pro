from flask import Blueprint, redirect, url_for, jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from api.services.oauth_service import oauth, OAuthService
from api.models.user import User

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/providers')
def get_providers():
    """Get list of configured OAuth providers"""
    providers = []
    
    if OAuthService.is_provider_configured('google'):
        providers.append({'name': 'google', 'display_name': 'Google'})
    
    if OAuthService.is_provider_configured('azure'):
        providers.append({'name': 'azure', 'display_name': 'Microsoft'})
    
    return jsonify({'providers': providers})

@auth_bp.route('/login/<provider>')
def oauth_login(provider):
    """Initiate OAuth login"""
    if provider not in ['google', 'azure']:
        return jsonify({'error': 'Invalid provider'}), 400
    
    if not OAuthService.is_provider_configured(provider):
        return jsonify({'error': f'{provider} OAuth not configured'}), 400
    
    client = oauth.create_client(provider)
    redirect_uri = url_for('auth.oauth_callback', provider=provider, _external=True)
    return client.authorize_redirect(redirect_uri)

@auth_bp.route('/callback/<provider>')
def oauth_callback(provider):
    """OAuth callback handler"""
    if provider not in ['google', 'azure']:
        return jsonify({'error': 'Invalid provider'}), 400
    
    try:
        client = oauth.create_client(provider)
        token = client.authorize_access_token()
        user_info = token.get('userinfo')
        
        if not user_info:
            user_info = client.userinfo()
        
        # Get or create user
        user = OAuthService.get_or_create_oauth_user(provider, user_info)
        
        if not user.is_active:
            return redirect('/?error=account_disabled')
        
        # Create JWT token
        access_token = create_access_token(identity=str(user.id))
        
        # Redirect to frontend with token
        return redirect(f'/?token={access_token}')
    
    except Exception as e:
        return redirect(f'/?error=oauth_failed&message={str(e)}')

@auth_bp.route('/me')
@jwt_required()
def get_current_user():
    """Get current user info"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@auth_bp.route('/activity')
@jwt_required()
def get_activity_log():
    """Get current user's activity log"""
    from api.models.activity_log import ActivityLog
    
    current_user_id = get_jwt_identity()
    
    # Get recent activity (last 20)
    activities = ActivityLog.query.filter_by(user_id=current_user_id)\
        .order_by(ActivityLog.timestamp.desc())\
        .limit(20)\
        .all()
        
    return jsonify([{
        'action': a.action,
        'details': a.details,
        'timestamp': a.timestamp.isoformat()
    } for a in activities])

@auth_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_current_user():
    """Update current user info"""
    from werkzeug.security import generate_password_hash, check_password_hash
    from api.middleware.input_validation import validate_password_complexity, validate_email
    from api.extensions import db
    from api.models.activity_log import ActivityLog
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
        
    data = request.get_json()
    
    # Update username
    if 'username' in data and data['username'] != user.username:
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': 'Username already exists'}), 409
        user.username = data['username']
        
    # Update email
    if 'email' in data and data['email'] != user.email:
        if not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already exists'}), 409
        user.email = data['email']
        
    # Update password
    if 'password' in data and data['password']:
        # Require current password
        if not data.get('current_password'):
            return jsonify({'error': 'Current password is required to set a new password'}), 400
            
        if not user.password_hash or not check_password_hash(user.password_hash, data['current_password']):
            # Log failed attempt
            log = ActivityLog(
                user_id=user.id,
                action='failed_password_change',
                details='Incorrect current password'
            )
            db.session.add(log)
            db.session.commit()
            return jsonify({'error': 'Incorrect current password'}), 401
            
        is_valid, error_message = validate_password_complexity(data['password'])
        if not is_valid:
            return jsonify({'error': error_message}), 400
            
        user.password_hash = generate_password_hash(data['password'])
        
        # Log success
        log = ActivityLog(
            user_id=user.id,
            action='password_change',
            details='Password updated successfully'
        )
        db.session.add(log)
        
    try:
        db.session.commit()
        return jsonify({
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to update profile'}), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint"""
    # JWT tokens are stateless, so just return success
    # Client should delete the token
    return jsonify({'message': 'Logged out successfully'})

@auth_bp.route('/login', methods=['POST'])
def login():
    """Username/Password login"""
    from werkzeug.security import check_password_hash
    from api.models.activity_log import ActivityLog
    from api.extensions import db
    
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing username or password'}), 400
        
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.password_hash or not check_password_hash(user.password_hash, data['password']):
        # Log failed login if user exists
        if user:
            log = ActivityLog(
                user_id=user.id,
                action='failed_login',
                details='Invalid credentials'
            )
            db.session.add(log)
            db.session.commit()
            
        return jsonify({'error': 'Invalid credentials'}), 401
        
    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403
        
    # Log successful login
    log = ActivityLog(
        user_id=user.id,
        action='successful_login',
        details='User logged in'
    )
    db.session.add(log)
    db.session.commit()
        
    access_token = create_access_token(identity=str(user.id))
    return jsonify({
        'token': access_token,
        'user': user.to_dict()
    })

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    from werkzeug.security import generate_password_hash
    from api.extensions import db
    from api.models.role import Role
    from api.middleware.input_validation import validate_password_complexity
    
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data or 'email' not in data:
        return jsonify({'error': 'Missing required fields'}), 400
        
    is_valid, error_message = validate_password_complexity(data['password'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
        
    if User.query.filter((User.username == data['username']) | (User.email == data['email'])).first():
        return jsonify({'error': 'Username or email already exists'}), 409
        
    # Default role: user (or whatever is default)
    # For first user, maybe make admin? Or just default to 'user'
    default_role = Role.query.filter_by(name='user').first()
    
    new_user = User(
        username=data['username'],
        email=data['email'],
        password_hash=generate_password_hash(data['password']),
        role=default_role
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(new_user.id))
    return jsonify({
        'message': 'User registered successfully',
        'token': access_token,
        'user': new_user.to_dict()
    }), 201

@auth_bp.route('/invite', methods=['POST'])
@jwt_required()
def create_invite():
    """Create and send an invitation"""
    from api.models.invite import Invite
    from api.models.role import Role
    from api.services.notification_service import NotificationService
    from api.extensions import db
    from datetime import datetime, timedelta
    
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    # Check if user is admin (or has permission)
    if not user.role or user.role.name != 'admin':
        return jsonify({'error': 'Permission denied'}), 403
        
    data = request.get_json()
    if not data or 'email' not in data or 'role_id' not in data:
        return jsonify({'error': 'Missing email or role_id'}), 400
        
    email = data['email']
    role_id = data['role_id']
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        return jsonify({'error': 'User with this email already exists'}), 409
        
    # Check if valid role
    role = Role.query.get(role_id)
    if not role:
        return jsonify({'error': 'Invalid role'}), 400
        
    # Check for existing pending invite
    existing_invite = Invite.query.filter_by(email=email, is_used=False).first()
    if existing_invite:
        # Update existing invite
        existing_invite.expires_at = datetime.utcnow() + timedelta(hours=24)
        existing_invite.role_id = role_id
        existing_invite.created_by = current_user_id
        invite = existing_invite
    else:
        # Create new invite
        invite = Invite(
            email=email,
            role_id=role_id,
            created_by=current_user_id,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        db.session.add(invite)
    
    db.session.commit()
    
    # Send email
    if NotificationService.send_invite_email(email, invite.token, role.name):
        return jsonify({'message': 'Invitation sent successfully', 'token': invite.token}), 201
    else:
        return jsonify({'message': 'Invitation created but email failed', 'token': invite.token}), 201

@auth_bp.route('/invite/<token>', methods=['GET'])
def validate_invite(token):
    """Validate an invite token"""
    from api.models.invite import Invite
    from datetime import datetime
    
    invite = Invite.query.filter_by(token=token, is_used=False).first()
    
    if not invite:
        return jsonify({'valid': False, 'error': 'Invalid or used token'}), 404
        
    if invite.expires_at < datetime.utcnow():
        return jsonify({'valid': False, 'error': 'Token expired'}), 400
        
    return jsonify({
        'valid': True, 
        'email': invite.email, 
        'role': invite.role.name
    })

@auth_bp.route('/register/invite', methods=['POST'])
def register_with_invite():
    """Register using an invite token"""
    from api.models.invite import Invite
    from werkzeug.security import generate_password_hash
    from api.extensions import db
    from datetime import datetime
    from api.middleware.input_validation import validate_password_complexity
    
    data = request.get_json()
    if not data or 'token' not in data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    is_valid, error_message = validate_password_complexity(data['password'])
    if not is_valid:
        return jsonify({'error': error_message}), 400
        
    token = data['token']
    invite = Invite.query.filter_by(token=token, is_used=False).first()
    
    if not invite:
        return jsonify({'error': 'Invalid or used token'}), 404
        
    if invite.expires_at < datetime.utcnow():
        return jsonify({'error': 'Token expired'}), 400
        
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 409
        
    # Create user
    new_user = User(
        username=data['username'],
        email=invite.email, # Use email from invite
        password_hash=generate_password_hash(data['password']),
        role_id=invite.role_id
    )
    
    # Mark invite as used
    invite.is_used = True
    
    db.session.add(new_user)
    db.session.commit()
    
    access_token = create_access_token(identity=str(new_user.id))
    return jsonify({
        'message': 'User registered successfully',
        'token': access_token,
        'user': new_user.to_dict()
    }), 201
