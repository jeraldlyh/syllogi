from sqlmodel import Session

from db.models.notification import Notification, NotificationChannel
from db.notification import get_notifications


def _make_notification(**overrides) -> Notification:
    defaults = {
        "channel": NotificationChannel.discord,
        "webhook_url": "https://example.com/webhook",
        "enabled": True,
    }
    defaults.update(overrides)
    return Notification(**defaults)


class TestGetNotifications:
    def test_empty(self, session: Session):
        assert get_notifications(session) == []

    def test_returns_all(self, session: Session):
        notification = _make_notification()

        session.add(notification)
        session.commit()

        assert len(get_notifications(session)) == 1
