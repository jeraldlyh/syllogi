from fastapi import APIRouter

from db.notification import _get_notifications
from db.session import SessionDep

router = APIRouter()


@router.get(
    path="",
    summary="Get notifications",
    description="Retrieve a list of all notifications.",
)
async def get_notifications(session: SessionDep):
    notifications = _get_notifications(session=session)

    return [notification.to_dict() for notification in notifications]
