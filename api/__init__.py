from flask import Flask, jsonify, send_from_directory
from flask_compress import Compress
from flask_cors import CORS
# from flask_talisman import Talisman
from api.config import Config
import logging

def create_app(config_class=Config, init_scheduler=True):
    app = Flask(__name__, static_folder='../web', static_url_path='/static')
    app.config.from_object(config_class)
    
    # Initialize extensions
    from api.extensions import db, migrate, limiter, socketio, jwt
    from api.cache import cache
    
    Compress(app)
    cache.init_app(app)
    
    # Initialize rate limiter (increased for development)
    app.config['RATELIMIT_DEFAULT'] = '500 per hour'  # Increased from 50 to 500

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    socketio.init_app(app)
    jwt.init_app(app)
    
    # Initialize CORS (Allow all for development, restrict in prod)
    CORS(app)
    
    # Initialize Talisman (Security Headers)
    # Uncomment when flask-talisman is installed
    # csp = {
    #     'default-src': ["'self'"],
    #     'script-src': ["'self'", "'unsafe-inline'", 'cdn.jsdelivr.net', 'cdnjs.cloudflare.com'],
    #     'style-src': ["'self'", "'unsafe-inline'", 'cdnjs.cloudflare.com'],
    #     'img-src': ["'self'", 'data:'],
    #     'font-src': ["'self'", 'cdnjs.cloudflare.com'],
    # }
    # Talisman(app, force_https=False, content_security_policy=csp)
    
    # Register Blueprints
    from api.routes.scan_routes import scan_bp
    from api.routes.report_routes import report_bp
    from api.routes.ticket_routes import ticket_bp
    from api.routes.target_routes import target_bp
    from api.routes.target_group_routes import target_group_bp
    from api.routes.user_routes import user_bp
    from api.routes.vuln_routes import vuln_bp

    from api.routes.openvas_routes import openvas_bp
    from api.routes.report_routes import report_bp
    from api.routes.exploit_routes import exploit_bp
    from api.routes.schedule_routes import schedule_bp
    from api.routes.asset_routes import asset_bp
    from api.routes.ml_routes import ml_bp
    from api.routes.auth_routes import auth_bp
    from api.routes.role_routes import role_bp
    from api.routes.audit_routes import audit_bp
    from api.routes.dashboard_routes import dashboard_bp
    from api.routes.search_routes import search_bp
    from api.routes.team_routes import team_bp
    from api.routes.collaboration_routes import collab_bp
    from api.routes.notification_routes import notification_bp
    
    app.register_blueprint(target_bp)
    app.register_blueprint(scan_bp)
    app.register_blueprint(vuln_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(schedule_bp)
    app.register_blueprint(openvas_bp)
    app.register_blueprint(target_group_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(exploit_bp)
    app.register_blueprint(asset_bp)
    app.register_blueprint(ml_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(role_bp)
    app.register_blueprint(audit_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(team_bp)
    app.register_blueprint(collab_bp)
    app.register_blueprint(notification_bp)
    
    # Register WebSocket events
    from api import socket_events
    
    # Initialize OAuth
    from api.services.oauth_service import OAuthService
    OAuthService.init_app(app)
    
    # Initialize Scheduler Service
    if init_scheduler:
        from api.services.scheduler_service import SchedulerService
        app.scheduler_service = SchedulerService(app)
    
    # Initialize Scan Manager
    from api.services.scan_manager import ScanManager
    app.scan_manager = ScanManager(app)
    
    # Configure Logging
    from api.logger import configure_logging
    configure_logging(app)
    
    # Initialize Security Middleware
    from api.middleware import init_all_middleware
    init_all_middleware(app)
    
    # Register Error Handlers
    from api.error_handlers import register_error_handlers
    register_error_handlers(app)
    
    # Health Check
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Serve index.html at root
    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')
    
    return app
