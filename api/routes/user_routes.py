from flask import Blueprint, request
from api.db import DATABASE, generate_id

user_bp = Blueprint("user_bp", __name__)


# CREATE USER
@user_bp.route("/", methods=["POST"])
def create_user():
    data = request.json
    username = data.get("username")
    role = data.get("role", "viewer")

    if not username:
        return {"error": "username required"}, 400

    user = {
        "id": generate_id("users"),
        "username": username,
        "role": role
    }

    DATABASE["users"].append(user)
    return {"message": "user created", "user": user}, 201


# LIST USERS
@user_bp.route("/", methods=["GET"])
def list_users():
    return {"users": DATABASE["users"]}


# UPDATE USER
@user_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.json
    for u in DATABASE["users"]:
        if u["id"] == user_id:
            u.update(data)
            return {"message": "updated", "user": u}
    return {"error": "user not found"}, 404


# DELETE USER
@user_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    for u in DATABASE["users"]:
        if u["id"] == user_id:
            DATABASE["users"].remove(u)
            return {"message": "deleted"}
    return {"error": "user not found"}, 404
