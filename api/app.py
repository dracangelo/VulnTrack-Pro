from flask import Flask
from api.routes.scan_routes import scan_bp
from api.routes.report_routes import report_bp
from api.routes.ticket_routes import ticket_bp
from api.routes.target_routes import target_bp
from api.routes.group_routes import group_bp
from api.routes.user_routes import user_bp

def create_app():
    app = Flask(__name__)

    # BASIC CONFIG
    app.config["JSON_SORT_KEYS"] = False

    # REGISTER BLUEPRINTS
    app.register_blueprint(scan_bp, url_prefix="/api/scans")
    app.register_blueprint(report_bp, url_prefix="/api/reports")
    app.register_blueprint(ticket_bp, url_prefix="/api/tickets")
    app.register_blueprint(target_bp, url_prefix="/api/targets")
    app.register_blueprint(group_bp, url_prefix="/api/groups")
    app.register_blueprint(user_bp, url_prefix="/api/users")

    # HEALTH CHECK
    @app.route("/api/health", methods=["GET"])
    def health_check():
        return {"status": "ok", "message": "VaultBox API running"}

    return app
