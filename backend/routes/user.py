from fastapi import APIRouter
from lib.jellyfin import _get_jellyfin_users

router = APIRouter()


@router.get(path="/jellyfin")
async def get_jellyfin_users():
    users = _get_jellyfin_users()

    return [
        {
            "id": user.get("Id"),
            "name": user.get("Name"),
        }
        for user in users
    ]
