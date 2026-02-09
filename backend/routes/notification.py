from fastapi import APIRouter
from models.notification import Notification
from sqlmodel import select
from lib.db import SessionDep

router = APIRouter()


@router.get(path="")
async def get_notifications(session: SessionDep):
    notifications = session.exec(select(Notification)).all()

    return [notification.to_dict() for notification in notifications]
