from authlib.integrations.flask_client import OAuth
from flask import current_app
from api.extensions import db
from api.models.user import User
from api.models.role import Role
from datetime import datetime

oauth = OAuth()

class OAuthService:
    """OAuth2/OIDC authentication service"""
    
    @staticmethod
    def init_app(app):
        """Initialize OAuth providers"""
        oauth.init_app(app)
        
        # Google OAuth
        if app.config.get('GOOGLE_CLIENT_ID') and app.config.get('GOOGLE_CLIENT_SECRET'):
            oauth.register(
                name='google',
                client_id=app.config.get('GOOGLE_CLIENT_ID'),
                client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
                server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
        
        # Azure AD OAuth
        if app.config.get('AZURE_CLIENT_ID') and app.config.get('AZURE_CLIENT_SECRET'):
            oauth.register(
                name='azure',
                client_id=app.config.get('AZURE_CLIENT_ID'),
                client_secret=app.config.get('AZURE_CLIENT_SECRET'),
                server_metadata_url=f'https://login.microsoftonline.com/{app.config.get("AZURE_TENANT_ID", "common")}/v2.0/.well-known/openid-configuration',
                client_kwargs={'scope': 'openid email profile'}
            )
    
    @staticmethod
    def get_or_create_oauth_user(provider, user_info):
        """Get existing OAuth user or create new one"""
        oauth_id = user_info.get('sub')  # Standard OIDC claim
        email = user_info.get('email')
        name = user_info.get('name', email.split('@')[0] if email else 'user')
        
        # Check if user exists by OAuth ID
        user = User.query.filter_by(oauth_provider=provider, oauth_id=oauth_id).first()
        
        if not user:
            # Check if email exists (link accounts)
            user = User.query.filter_by(email=email).first()
            
            if user:
                # Link OAuth to existing account
                user.oauth_provider = provider
                user.oauth_id = oauth_id
            else:
                # Create new user with default Viewer role
                default_role = Role.query.filter_by(name='Viewer').first()
                if not default_role:
                    default_role = Role.query.first()
                
                user = User(
                    username=name,
                    email=email,
                    oauth_provider=provider,
                    oauth_id=oauth_id,
                    role_id=default_role.id if default_role else None,
                    is_active=True
                )
                db.session.add(user)
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return user
    
    @staticmethod
    def is_provider_configured(provider):
        """Check if OAuth provider is configured"""
        if provider == 'google':
            return bool(current_app.config.get('GOOGLE_CLIENT_ID'))
        elif provider == 'azure':
            return bool(current_app.config.get('AZURE_CLIENT_ID'))
        return False
