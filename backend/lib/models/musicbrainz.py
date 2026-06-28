from dataclasses import dataclass

from lib.models.metadata import ArtistInfo


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

    def to_artist_info(self, locale: str | None = None) -> ArtistInfo:
        """Convert to ArtistInfo."""

        aliases = self._get_aliases_by_locale(locale)
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
            aliases=aliases,
        )

    def _get_aliases_by_locale(self, locale: str | None = None) -> list[str]:
        """Filter aliases by removing user's browser locale, falling back to all aliases."""

        if not locale:
            return [alias.name for alias in self.aliases]

        lang = locale.split("-")[0].split("_")[0].lower()
        matches = [
            alias.name
            for alias in self.aliases
            if alias.locale
            and not alias.locale.lower().replace("_", "-").startswith(lang)
        ]

        if matches:
            return matches
        return [alias.name for alias in self.aliases]
