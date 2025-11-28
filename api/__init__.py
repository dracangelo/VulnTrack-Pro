from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from flask_talisman import Talisman
from api.config import Config
import logging

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../web', static_url_path='/static')
    app.config.from_object(config_class)
    
    # Initialize extensions
    from api.extensions import db, migrate, limiter, socketio
    
    # Initialize rate limiter (increased for development)
    app.config['RATELIMIT_DEFAULT'] = '500 per hour'  # Increased from 50 to 500

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    socketio.init_app(app)
    
    # Initialize CORS (Allow all for development, restrict in prod)
    CORS(app)
    
    # Initialize Talisman (Security Headers)
    # Disable HTTPS force for dev, allow inline scripts/styles for Tailwind/Chart.js
    csp = {
        'default-src': "'self'",
        'script-src': ["'self'", "'unsafe-inline'", "https://cdn.tailwindcss.com", "https://cdn.jsdelivr.net", "https://cdn.socket.io"],
        'style-src': ["'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net", "https://cdnjs.cloudflare.com"],
        'font-src': ["'self'", "https://cdnjs.cloudflare.com"],
    }
    Talisman(app, force_https=False, content_security_policy=csp)
    
    # Register Blueprints
    from api.routes.scan_routes import scan_bp
    from api.routes.report_routes import report_bp
    from api.routes.ticket_routes import ticket_bp
    from api.routes.target_routes import target_bp
    from api.routes.target_group_routes import target_group_bp
    from api.routes.user_routes import user_bp
    from api.routes.vuln_routes import vuln_bp

    from api.routes.openvas_routes import openvas_bp
    from api.routes.schedule_routes import schedule_bp

    app.register_blueprint(scan_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(target_bp)
    app.register_blueprint(target_group_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(vuln_bp)

    app.register_blueprint(openvas_bp)
    app.register_blueprint(schedule_bp)
    
    # Register WebSocket events
    from api import socket_events
    
    # Initialize Scheduler Service
    from api.services.scheduler_service import SchedulerService
    app.scheduler_service = SchedulerService(app)
    
    # Configure Logging
    from api.logger import configure_logging
    configure_logging(app)
    
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
