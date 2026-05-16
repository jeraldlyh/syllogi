from dataclasses import dataclass


@dataclass
class JellyfinUser:
    """A user in Jellyfin."""

    def __init__(
        self,
        id: str,
        name: str,
    ):
        self.id = id
        self.name = name

    def to_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass
class JellyfinTrack:
    """A track in Jellyfin."""

    def __init__(
        self,
        id: str,
        track_name: str,
        album_name: str,
        album_id: str,
        musicbrainz_id: str,
        artists: list[str],
        duration_ticks: int,
        year: str,
    ):
        self.id = id
        self.track_name = track_name
        self.album_name = album_name
        self.album_id = album_id
        self.musicbrainz_id = musicbrainz_id
        self.artists = artists
        self.duration_ticks = duration_ticks
        self.year = year

    def is_not_found(self) -> bool:
        return not self.id or self.id == ""

    def to_dict(self) -> dict[str, str | int | list[str]]:
        return {
            "id": self.id,
            "track_name": self.track_name,
            "album_name": self.album_name,
            "album_id": self.album_id,
            "musicbrainz_id": self.musicbrainz_id,
            "artists": self.artists,
            "duration_ticks": self.duration_ticks,
            "year": self.year,
        }


@dataclass
class JellyfinPlaylist:
    """A playlist in Jellyfin."""

    def __init__(
        self,
        id: str,
        name: str,
    ):
        self.id = id
        self.name = name

    def to_dict(self) -> dict[str, str | int]:
        return {
            "id": self.id,
            "name": self.name,
        }


@dataclass
class JellyfinLibrary:
    """A virtual folder (library) in Jellyfin."""

    def __init__(
        self,
        name: str,
        locations: list[str],
        collection_type: str,
        item_id: str,
        refresh_status: str,
    ):
        self.name = name
        self.locations = locations
        self.collection_type = collection_type
        self.item_id = item_id
        self.refresh_status = refresh_status

    def to_dict(self) -> dict[str, str | list[str]]:
        return {
            "name": self.name,
            "locations": self.locations,
            "collection_type": self.collection_type,
            "item_id": self.item_id,
            "refresh_status": self.refresh_status,
        }
