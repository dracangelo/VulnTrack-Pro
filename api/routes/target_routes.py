from flask import Blueprint, request
from api.db import DATABASE, generate_id

target_bp = Blueprint("target_bp", __name__)

# CREATE
@target_bp.route("/", methods=["POST"])
def create_target():
    data = request.json
    target_name = data.get("name")
    ip = data.get("ip")

    if not target_name or not ip:
        return {"error": "name and ip are required"}, 400

    target = {
        "id": generate_id("targets"),
        "name": target_name,
        "ip": ip
    }

    DATABASE["targets"].append(target)
    return {"message": "target created", "target": target}, 201


# READ ALL
@target_bp.route("/", methods=["GET"])
def list_targets():
    return {"targets": DATABASE["targets"]}, 200


# READ ONE
@target_bp.route("/<int:target_id>", methods=["GET"])
def get_target(target_id):
    for t in DATABASE["targets"]:
        if t["id"] == target_id:
            return t
    return {"error": "target not found"}, 404


# UPDATE
@target_bp.route("/<int:target_id>", methods=["PUT"])
def update_target(target_id):
    data = request.json
    for t in DATABASE["targets"]:
        if t["id"] == target_id:
            t.update(data)
            return {"message": "updated", "target": t}
    return {"error": "target not found"}, 404


# DELETE
@target_bp.route("/<int:target_id>", methods=["DELETE"])
def delete_target(target_id):
    for t in DATABASE["targets"]:
        if t["id"] == target_id:
            DATABASE["targets"].remove(t)
            return {"message": "deleted"}
    return {"error": "target not found"}, 404
