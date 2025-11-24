from flask import Flask
from api.config import Config
from api.extensions import db
from flask_migrate import Migrate

migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__, static_folder='../web', static_url_path='/static')
    app.config.from_object(config_class)
    
    # Default Rate Limit
    app.config['RATELIMIT_DEFAULT'] = "200 per day; 50 per hour"

    db.init_app(app)
    migrate.init_app(app, db)
    
    # Security Extensions
    from api.extensions import limiter
    from flask_cors import CORS
    from flask_talisman import Talisman
    
    # Initialize Limiter
    limiter.init_app(app)
    
    # Initialize CORS (Allow all for development, restrict in prod)
    CORS(app)
    
    # Initialize Talisman (Security Headers)
    # Disable HTTPS force for dev, allow inline scripts/styles for Tailwind/Chart.js
    csp = {
        'default-src': '\'self\'',
        'script-src': ['\'self\'', '\'unsafe-inline\'', 'cdn.tailwindcss.com', 'cdn.jsdelivr.net'],
        'style-src': ['\'self\'', '\'unsafe-inline\'', 'cdn.tailwindcss.com'],
        'img-src': ['\'self\'', 'data:', '*']
    }
    Talisman(app, force_https=False, content_security_policy=csp)

    # Register models so Alembic can see them
    from api import models
    from api.models.activity_log import ActivityLog

    # Register Blueprints
    from api.routes.scan_routes import scan_bp
    from api.routes.report_routes import report_bp
    from api.routes.ticket_routes import ticket_bp
    from api.routes.target_routes import target_bp
    from api.routes.target_group_routes import target_group_bp
    from api.routes.user_routes import user_bp
    from api.routes.vuln_routes import vuln_bp

    app.register_blueprint(scan_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(ticket_bp)
    app.register_blueprint(target_bp)
    app.register_blueprint(target_group_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(vuln_bp)
    
    # Configure Logging
    from api.logger import configure_logging
    configure_logging(app)
    
    # Register Error Handlers
    from api.errors import register_error_handlers
    register_error_handlers(app)

    @app.route('/health')
    def health():
        return {'status': 'healthy'}

    @app.route('/')
    def index():
        return app.send_static_file('index.html')

    @app.route('/static/<path:path>')
    def send_js(path):
        return app.send_static_file(path)

    return app
