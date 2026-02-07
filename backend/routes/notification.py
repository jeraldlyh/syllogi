from flask import Blueprint, jsonify
from db.notification import Notification

bp = Blueprint("notification", __name__)


@bp.get("/")
def health():
    rows = Notification.query.all()
    return jsonify(status="ok")
