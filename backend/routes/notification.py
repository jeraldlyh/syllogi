from flask import Blueprint
from models.notification import Notification

bp = Blueprint("notification", __name__)


@bp.get("/")
def get_notifications():
    notification = Notification.query.first()

    if notification:
        return notification.to_dict()
    return Notification.get_default()
