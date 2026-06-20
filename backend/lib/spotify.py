import logging

from spotapi.playlist import PublicPlaylist

from lib.models.common import ExternalSync, ExternalTrack


logger = logging.getLogger(__name__)


def get_spotify_playlist(playlist_id: str) -> ExternalSync:
    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info()

    thumbnail_metadata = max(
        playlist_info["data"]["playlistV2"]["ownerV2"]["data"]["avatar"]["sources"],
        key=lambda x: x.get("height"),
    )

    return ExternalSync(
        id=playlist_id,
        name=playlist.get_playlist_info()["data"]["playlistV2"]["name"],
        total=playlist.get_playlist_info()["data"]["playlistV2"]["content"][
            "totalCount"
        ],
        thumbnail_url=thumbnail_metadata.get("url"),
    )


def get_spotify_playlist_songs(playlist_id: str) -> list[ExternalTrack]:
    offset = 0
    limit = 50
    songs: list[ExternalTrack] = []

    playlist = PublicPlaylist(playlist_id)
    playlist_info = playlist.get_playlist_info(limit=limit)

    while offset < playlist_info["data"]["playlistV2"]["content"]["totalCount"]:
        for item in playlist_info["data"]["playlistV2"]["content"]["items"]:
            album_metadata = item["itemV3"]["data"]["identityTrait"][
                "contentHierarchyParent"
            ]
            song = ExternalTrack(
                artist_name=item["itemV2"]["data"]["albumOfTrack"]["artists"]["items"][
                    0
                ]["profile"]["name"],
                year=album_metadata["publishingMetadataTrait"]["firstPublishedAt"][
                    "isoString"
                ][:4],
                track_name=item["itemV2"]["data"]["name"],
                duration=item["itemV3"]["data"]["consumptionExperienceTrait"][
                    "duration"
                ]["seconds"],
                album_name=album_metadata["identityTrait"]["name"],
            )
            songs.append(song)
        offset += limit
        playlist_info = playlist.get_playlist_info(offset=offset, limit=limit)
        logger.info(f"Fetched {len(songs)} songs...")
    logger.info(f"Total songs fetched from Spotify playlist: {len(songs)}")

    return songs
