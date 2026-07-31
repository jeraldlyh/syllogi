import pytest
from sqlmodel import Session, SQLModel, create_engine

from db.models.download_session import DownloadSession
from db.models.music_server_user import MusicServerUser
from db.models.notification import Notification
from db.models.recommendation import (
    Recommendation,
    RecommendationSession,
    RecommendationSessionTrack,
)
from db.models.sync import Sync, SyncSession, SyncSessionTrack
from db.models.user import User


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
