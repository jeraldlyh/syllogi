from dataclasses import dataclass

from lib.models.metadata import ArtistInfo, ArtistRecording


@dataclass
class MusicbrainzArtistAlias:
    sort_name: str
    name: str
    locale: str | None
    type: str | None
    primary: bool | None
    begin_date: str | None
    end_date: str | None


@dataclass
class MusicbrainzArtistArea:
    id: str
    type: str
    type_id: str
    name: str
    sort_name: str
    life_span: dict[str, str | None]


@dataclass
class MusicbrainzArtistTag:
    count: int
    name: str


@dataclass
class MusicbrainzRecording:
    id: str
    title: str
    length: int | None
    disambiguation: str
    video: bool


@dataclass
class MusicbrainzArtist:
    id: str
    type: str
    type_id: str
    score: int
    gender_id: str
    name: str
    sort_name: str
    gender: str
    country: str
    area: MusicbrainzArtistArea
    begin_area: MusicbrainzArtistArea
    ipis: list[str]
    isnis: list[str]
    life_span: dict[str, str | None]
    aliases: list[MusicbrainzArtistAlias]
    tags: list[MusicbrainzArtistTag]
    recordings: list[MusicbrainzRecording]

    def to_artist_recording(self) -> list[ArtistRecording]:
        """Convert recordings to ArtistRecording list."""

        return [
            ArtistRecording(
                title=recording.title,
                duration_ms=recording.length,
                disambiguation=recording.disambiguation,
            )
            for recording in self.recordings
        ]

    def to_artist_info(self) -> ArtistInfo:
        """Convert to ArtistInfo."""
        return ArtistInfo(
            id=self.id,
            name=self.name,
            type=self.type,
            country=self.country,
            gender=self.gender,
            life_span=self.life_span,
            area=self.area.name if self.area else None,
            begin_area=self.begin_area.name if self.begin_area else None,
            tags=[tag.name for tag in self.tags],
            aliases=[alias.name for alias in self.aliases],
            recordings=self.to_artist_recording(),
        )
