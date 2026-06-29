from dataclasses import dataclass


@dataclass
class DeezerTrack:
    """A track result from the Deezer API."""

    title: str
    album_name: str
    image_url: str | None
    duration: int
