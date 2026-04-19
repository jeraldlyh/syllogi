from typing import Annotated

from fastapi import APIRouter, Query

from lib.track import find_track, get_recommendations

router = APIRouter()


@router.get(
    path="",
    summary="Find a track",
    description="Look up a track by artist and title and return the best match.",
    responses={
        200: {
            "description": "Track matched successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "artist_name": "",
                            "track": {
                                "id": "e0c7947223ed30eff55e5aa42091aec6",
                                "name": "GANADARA (Feat. IU)",
                            },
                            "album": {
                                "id": "e9636433bd6eeb3e4297bc90d4ac6aa9",
                                "name": "GANADARA",
                            },
                            "search_name": "GANADARA",
                            "exists": True,
                        },
                    }
                }
            },
        }
    },
)
def _find_track(
    artist_name: Annotated[str, Query(description="Artist name")],
    title: Annotated[str, Query(description="Track title")],
):
    return find_track(artist_name, title, album_name="", year="", duration=0)


@router.get(
    path="/recommendations",
    summary="Get track recommendations",
    description="Get track recommendations based on a given track.",
)
def _get_recommendations(
    user: Annotated[str, Query(description="LastFM username")],
):
    result = get_recommendations(user=user)

    return result
