from flask import Blueprint
from lib.jellyfin import _get_jellyfin_users

bp = Blueprint("user", __name__)


@bp.get("/jellyfin")
def get_jellyfin_users():
    users = _get_jellyfin_users()

    return [
        {
            "id": user.get("Id"),
            "name": user.get("Name"),
        }
        for user in users
    ]
