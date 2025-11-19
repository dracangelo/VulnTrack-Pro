from flask import Blueprint, request
from api.db import DATABASE, generate_id

group_bp = Blueprint("group_bp", __name__)


# CREATE GROUP
@group_bp.route("/", methods=["POST"])
def create_group():
    data = request.json
    name = data.get("name")
    targets = data.get("targets", [])

    if not name:
        return {"error": "name required"}, 400

    group = {
        "id": generate_id("groups"),
        "name": name,
        "targets": targets,
    }

    DATABASE["groups"].append(group)
    return {"message": "group created", "group": group}, 201


# LIST GROUPS
@group_bp.route("/", methods=["GET"])
def list_groups():
    return {"groups": DATABASE["groups"]}


# GET ONE GROUP
@group_bp.route("/<int:group_id>", methods=["GET"])
def get_group(group_id):
    for g in DATABASE["groups"]:
        if g["id"] == group_id:
            return g
    return {"error": "group not found"}, 404


# UPDATE GROUP
@group_bp.route("/<int:group_id>", methods=["PUT"])
def update_group(group_id):
    data = request.json
    for g in DATABASE["groups"]:
        if g["id"] == group_id:
            g.update(data)
            return {"message": "updated", "group": g}
    return {"error": "group not found"}, 404


# DELETE GROUP
@group_bp.route("/<int:group_id>", methods=["DELETE"])
def delete_group(group_id):
    for g in DATABASE["groups"]:
        if g["id"] == group_id:
            DATABASE["groups"].remove(g)
            return {"message": "deleted"}
    return {"error": "group not found"}, 404
