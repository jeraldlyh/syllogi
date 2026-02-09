from fastapi import APIRouter

from db.notification import _get_all_notifications
from db.session import SessionDep

router = APIRouter()


@router.get(path="")
async def get_notifications(session: SessionDep):
    notifications = _get_all_notifications(session=session)

    return [notification.to_dict() for notification in notifications]
