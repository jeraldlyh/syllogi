from pydantic import BaseModel


class BlendUser(BaseModel):
    """A user included in a blend recommendation."""

    model_config = {"frozen": True}
    name: str
    lastfm_username: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "lastfm_username": self.lastfm_username,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> "BlendUser":
        return cls(name=data["name"], lastfm_username=data["lastfm_username"])
