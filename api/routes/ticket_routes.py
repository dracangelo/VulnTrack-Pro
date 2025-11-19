from flask import Blueprint

ticket_bp = Blueprint("ticket_bp", __name__)

@ticket_bp.route("/", methods=["GET"])
def list_tickets():
    # TODO: return list of tickets
    return {"tickets": []}
