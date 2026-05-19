from datetime import datetime, timezone
from typing import Iterable, TypedDict, Any

import httpx


class EmbedField(TypedDict):
    name: str
    value: str | int
    inline: bool


def _to_iso8601(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_color_hex(c: int | str) -> int:
    if isinstance(c, int):
        return c
    return int(c.lstrip("#"), 16)


async def send_discord_notification(
    webhook_url: str | None,
    *,
    content: str | None = None,
    title: str | None = None,
    description: str | None = None,
    url: str | None = None,
    color: int | str = "#5865F2",
    fields: Iterable[EmbedField] | None = None,
    footer_text: str | None = None,
    footer_icon_url: str | None = None,
    thumbnail_url: str | None = None,
    image_url: str | None = None,
    author_name: str | None = None,
    author_url: str | None = None,
    author_icon_url: str | None = None,
    timestamp: datetime | bool | None = None,
    username: str | None = None,
    avatar_url: str | None = None,
    timeout: float = 15.0,
) -> dict | None:
    if not webhook_url:
        return

    embed: dict = {"color": _to_color_hex(color)}

    if title:
        embed["title"] = title
    if description:
        embed["description"] = description
    if url:
        embed["url"] = url
    if author_name or author_url or author_icon_url:
        author = {}
        if author_name:
            author["name"] = author_name
        if author_url:
            author["url"] = author_url
        if author_icon_url:
            author["icon_url"] = author_icon_url
        embed["author"] = author
    if thumbnail_url:
        embed["thumbnail_url"] = thumbnail_url
    if image_url:
        embed["image_url"] = image_url
    if footer_text or footer_icon_url:
        footer = {}
        if footer_text:
            footer["text"] = footer_text
        if footer_icon_url:
            footer["icon_url"] = footer_icon_url
        embed["footer"] = footer
    if timestamp:
        dt = datetime.now(timezone.utc) if timestamp is True else timestamp
        embed["timestamp"] = _to_iso8601(dt)
    if fields:
        field_list: list[dict[str, Any]] = []

        for entry in fields:
            name = str(entry["name"])
            value = str(entry["value"])
            inline = bool(entry["inline"]) if "inline" in entry else True
            item = {"name": name, "value": value, "inline": inline}
            field_list.append(item)
        embed["fields"] = field_list

    payload: dict[str, Any] = {"embeds": [embed]}

    if content:
        payload["content"] = content
    if username:
        payload["username"] = username
    if avatar_url:
        payload["avatar_url"] = avatar_url

    async with httpx.AsyncClient() as client:
        response = await client.post(webhook_url, json=payload, timeout=timeout)
    response.raise_for_status()
    if response.status_code == 204 or not response.content:
        return None
    return response.json()
