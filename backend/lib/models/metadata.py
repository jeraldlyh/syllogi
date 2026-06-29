from dataclasses import dataclass


@dataclass
class ArtistRecording:
    """A recording (track) by an artist."""

    title: str
    duration_ms: int | None
    disambiguation: str
    album_name: str

    def get_duration(self) -> int:
        if not self.duration_ms:
            return 0
        return self.duration_ms // 1000

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "title": self.title,
            "duration": self.duration_ms // 1000 if self.duration_ms else 0,
            "disambiguation": self.disambiguation,
            "album_name": self.album_name,
        }

    def __eq__(self, other):
        if not isinstance(other, ArtistRecording):
            return NotImplemented
        return self.title.casefold() == other.title.casefold()

    def __hash__(self):
        return hash(self.title.casefold())


@dataclass
class ArtistInfo:
    """Full artist metadata, including optional related data."""

    MAX_ALIASES = 5

    id: str
    name: str
    type: str
    country: str
    gender: str
    life_span: dict[str, str | None]
    area: str | None
    begin_area: str | None
    tags: list[str]
    aliases: list[str]
    image_url: str | None = None
    num_of_fans: int | None = None

    def to_dict(self) -> dict[str, str | dict | list | int | None]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "country": self.country,
            "gender": self.gender,
            "life_span": self.life_span,
            "area": self.area,
            "begin_area": self.begin_area,
            "tags": self.tags,
            "aliases": self.aliases[: self.MAX_ALIASES],
            "image_url": self.image_url,
            "num_of_fans": self.num_of_fans,
        }
