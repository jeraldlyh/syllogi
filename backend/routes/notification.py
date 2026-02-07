from fastapi import APIRouter
from models.notification import Notification

router = APIRouter()


@router.get(path="")
async def get_notifications():
    notification = Notification.query.first()

    if notification:
        return notification.to_dict()
    return Notification.get_default()
