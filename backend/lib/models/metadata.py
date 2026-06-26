from dataclasses import dataclass


@dataclass
class ArtistRecording:
    """A recording (track) by an artist."""

    title: str
    duration_ms: int | None
    disambiguation: str

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "title": self.title,
            "duration": self.duration_ms // 1000 if self.duration_ms else 0,
            "disambiguation": self.disambiguation,
        }


@dataclass
class ArtistInfo:
    """Full artist metadata, including optional related data."""

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

    def to_dict(self) -> dict[str, str | dict | list | None]:
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
            "aliases": self.aliases,
        }
