from flask import Blueprint
from lib.jellyfin import get_jellyfin_users

bp = Blueprint("user", __name__)


@bp.get("/jellyfin")
def _get_jellyfin_users():
    users = get_jellyfin_users()

    return [
        {
            "id": user.get("Id"),
            "name": user.get("Name"),
        }
        for user in users
    ]
