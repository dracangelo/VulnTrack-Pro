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
        access_token = create_access_token(identity=user.id)
        
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

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout endpoint"""
    # JWT tokens are stateless, so just return success
    # Client should delete the token
    return jsonify({'message': 'Logged out successfully'})
