from dataclasses import dataclass


@dataclass
class BlendUser:
    """A user included in a blend recommendation."""

    def __init__(self, name: str, lastfm_username: str):
        self.name = name
        self.lastfm_username = lastfm_username

    def __eq__(self, other) -> bool:
        return (
            self.name == other.name
            and self.lastfm_username == other.lastfm_username
        )

    def __hash__(self) -> int:
        return hash((self.name, self.lastfm_username))

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "lastfm_username": self.lastfm_username,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "BlendUser":
        return cls(name=data["name"], lastfm_username=data["lastfm_username"])
