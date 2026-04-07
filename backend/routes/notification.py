from fastapi import APIRouter

from db.notification import _get_notifications
from db.session import SessionDep

router = APIRouter()


@router.get(
    path="",
    summary="Get notifications",
    description="Retrieve a list of all notifications.",
    responses={
        200: {
            "description": "Notifications retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "4f6aaf48-86a9-40ba-95dd-cf77c0ca2f88",
                                "title": "Sync completed",
                                "message": "Playlist sync finished successfully",
                                "created_at": "2026-04-05T11:22:33Z",
                            }
                        ],
                    }
                }
            },
        }
    },
)
async def get_notifications(session: SessionDep):
    notifications = _get_notifications(session=session)

    return [notification.to_dict() for notification in notifications]
