from flask import Blueprint

report_bp = Blueprint("report_bp", __name__)

@report_bp.route("/", methods=["GET"])
def list_reports():
    # TODO: return list of generated reports
    return {"reports": []}
