from flask import Blueprint, request

scan_bp = Blueprint("scan_bp", __name__)

# Add target to scanning queue
@scan_bp.route("/add-target", methods=["POST"])
def add_target():
    data = request.json
    target = data.get("target")

    if not target:
        return {"error": "target is required"}, 400

    # TODO: add target persistence + queue
    return {"message": "target added", "target": target}
