from typing import Annotated

from fastapi import APIRouter, Query

from lib.track import _find_track

router = APIRouter()


@router.get(
    path="",
    summary="Find a track",
    description="Look up a track by artist and title and return the best match.",
)
async def find_track(
    artist_name: Annotated[str, Query(description="Artist name")],
    title: Annotated[str, Query(description="Track title")],
):
    return _find_track(artist_name, title, album_name="", year="", duration=0)
