from dataclasses import dataclass


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
