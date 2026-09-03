import uuid
from typing import Any, cast

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from lib.mixin.metadata import TimestampMixin
from lib.mixin.serializer import SerializerMixin


class LibraryTrack(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    path: str = Field(max_length=1024, nullable=False, unique=True, index=True)
    filename: str = Field(max_length=512, nullable=False)
    directory: str = Field(default="", max_length=1024, nullable=False, index=True)
    format: str = Field(max_length=16, nullable=False, index=True)

    size: int = Field(default=0, sa_type=cast(type[Any], sa.BigInteger), nullable=False)
    duration: int = Field(default=0, nullable=False)
    mtime: float = Field(default=0.0, nullable=False)

    title: str = Field(default="", max_length=512, nullable=False)
    artist: str = Field(default="", max_length=512, nullable=False)
    album: str = Field(default="", max_length=512, nullable=False)
    date: str = Field(default="", max_length=32, nullable=False)
    genres: list[str] = Field(default_factory=list, sa_type=sa.JSON, nullable=False)
    musicbrainz_id: str = Field(default="", max_length=64, nullable=False)

    has_lyrics: bool = Field(default=False, nullable=False, index=True)
    is_synced_lyrics: bool = Field(default=False, nullable=False)

    def filled_fields(self) -> list[str]:
        """List the tag fields that carry a value on this file."""

        filled = []

        if self.title:
            filled.append("title")
        if self.artist:
            filled.append("artist")
        if self.album:
            filled.append("album")
        if self.date:
            filled.append("date")
        if self.genres:
            filled.append("genres")
        if self.has_lyrics:
            filled.append("lyrics")
        if self.musicbrainz_id:
            filled.append("musicbrainz_id")
        return filled

    def to_dict(self, lyrics: str | None = None) -> dict:
        tags: dict[str, Any] = {
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "date": self.date,
            "genres": list(self.genres),
            "musicbrainz_id": self.musicbrainz_id,
        }

        if lyrics is not None:
            tags["lyrics"] = lyrics

        return {
            "path": self.path,
            "filename": self.filename,
            "directory": self.directory,
            "format": self.format,
            "size": self.size,
            "duration": self.duration,
            "has_lyrics": self.has_lyrics,
            "is_synced_lyrics": self.is_synced_lyrics,
            "filled_fields": self.filled_fields(),
            "tags": tags,
        }

    def __str__(self) -> str:
        return f"LibraryTrack(path={self.path!r}, format={self.format!r})"


class LibraryFolder(TimestampMixin, SerializerMixin, SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True, nullable=False)

    path: str = Field(max_length=1024, nullable=False, unique=True, index=True)

    def to_dict(self) -> dict:
        return {"path": self.path}

    def __str__(self) -> str:
        return f"LibraryFolder(path={self.path!r})"
