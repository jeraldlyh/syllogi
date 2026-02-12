import uuid
from db.models.import_session import ImportSession, ImportSessionTrack, TrackListKind
from db.session import SessionDep


def _create_import_session(session: SessionDep, import_session: ImportSession) -> None:
    session.add(import_session)
    session.commit()
    session.refresh(import_session)


def _build_tracks(
    import_session_id: uuid.UUID, names: list[str], kind: TrackListKind
) -> list[ImportSessionTrack]:
    return [
        ImportSessionTrack(import_session_id=import_session_id, kind=kind, name=name)
        for name in names
    ]
