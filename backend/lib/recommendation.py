import logging
import uuid
from typing import Any

from fastapi import HTTPException, status

from db.models.recommendation import (
    Recommendation,
    RecommendationProvider,
    RecommendationSession,
    RecommendationStatus,
    RecommendationStrategy,
    RecommendationTrackType,
)
from db.music_server_user import get_music_server_user_by_username
from db.recommendation import get_recommendation_by_id
from db.recommendation_session import (
    build_recommendation_session_tracks,
    create_recommendation_session,
    format_recommendation_session_track_names,
    get_recommendation_session_by_id,
    update_recommendation_session,
)
from db.session import get_isolated_session
from lib.crypto import decrypt
from lib.download import download_missing_tracks
from lib.models.provider import ProviderTrack
from lib.providers import get_provider_enum, get_recommendation_provider
from lib.providers.base import MusicPlaylistProvider
from lib.models.common import RecommendationTrack
from lib.providers.base import RecommendationSourceProvider
from lib.track import find_track, reconcile_after_download, resolve_tracks
from lib.utils import get_now, truncate

logger = logging.getLogger(__name__)


async def get_recommendations(
    recommendation_provider: RecommendationSourceProvider,
    music_provider: MusicPlaylistProvider,
    strategy: RecommendationStrategy,
    num_recommendations: int,
    username: str,
    blend_users: list[tuple[str, str]] | None,
) -> tuple[list[RecommendationTrack], list[RecommendationTrack], list[ProviderTrack]]:
    """Generate track recomendations based on the specified strategy and user listening history."""

    match strategy:
        case RecommendationStrategy.top_tracks:
            all_tracks = await recommendation_provider.get_top_tracks(
                username=username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.recent_tracks:
            all_tracks = await recommendation_provider.get_recent_tracks(
                username=username,
                limit=num_recommendations,
            )
        case RecommendationStrategy.mixed:
            recent_limit = round(num_recommendations * 0.5)

            recent_tracks = await recommendation_provider.get_recent_tracks(
                username=username,
                limit=recent_limit,
            )
            top_tracks = await recommendation_provider.get_top_tracks(
                username=username,
                limit=num_recommendations - recent_limit,
            )

            all_tracks = recent_tracks + top_tracks
        case RecommendationStrategy.blend:
            if not blend_users:
                raise ValueError("blend_users required for blend strategy")

            per_user_limit = max(1, num_recommendations // (2 * len(blend_users)))
            all_tracks = []

            for _, recommendation_provider_username in blend_users:
                recent = await recommendation_provider.get_recent_tracks(
                    username=recommendation_provider_username, limit=per_user_limit
                )
                top = await recommendation_provider.get_top_tracks(
                    username=recommendation_provider_username, limit=per_user_limit
                )
                all_tracks.extend(recent + top)

    missing: set[RecommendationTrack] = set()
    found: set[RecommendationTrack] = set()
    provider_tracks: list[ProviderTrack] = []

    for track in all_tracks:
        if len(found) + len(missing) >= num_recommendations:
            break

        similar_tracks = await recommendation_provider.get_similar_tracks(
            artist_name=track.artist_name,
            track_name=track.track_name,
            musicbrainz_id=track.musicbrainz_id,
        )

        has_missing = False
        for similar_track in similar_tracks:
            if len(found) + len(missing) >= num_recommendations:
                break

            if similar_track in found or similar_track in missing:
                continue

            provider_track = await find_track(
                provider=music_provider,
                artist_name=similar_track.artist_name,
                track_name=similar_track.track_name,
                album_name=similar_track.album_name,
                year="",
                duration=similar_track.duration,
            )

            if not provider_track.is_not_found():
                found.add(similar_track)
                provider_tracks.append(provider_track)

            if not has_missing and provider_track.is_not_found():
                missing.add(similar_track)
                has_missing = True

    return list(found), list(missing), provider_tracks


async def generate_recommendations_task(
    provider: MusicPlaylistProvider,
    recommendation_session_id: uuid.UUID,
    recommendation_id: uuid.UUID,
    blend_users: list[str] | None,
) -> Any:
    """Get track recommendations for a user based on their listening history in a background task."""

    with get_isolated_session() as session:
        recommendation_session: RecommendationSession | None = None

        try:
            recommendation = get_recommendation_by_id(
                session=session, recommendation_id=recommendation_id
            )
            if not recommendation:
                raise ValueError(
                    f"Unable to find recommendation setting: {recommendation_id}",
                )

            recommendation_session = get_recommendation_session_by_id(
                session=session, recommendation_session_id=recommendation_session_id
            )
            if not recommendation_session:
                raise ValueError(
                    f"Unable to find recommendation session: {recommendation_session_id}",
                )

            started_at = recommendation_session.started_at
            music_server_user = get_music_server_user_by_username(
                session=session,
                username=recommendation.username,
                provider=get_provider_enum(),
            )

            if not music_server_user:
                raise ValueError(
                    f"Unable to find music_server_user: {recommendation.username}"
                )

            recommendation_provider = get_recommendation_provider(
                recommendation.provider
            )

            if recommendation.provider == RecommendationProvider.listenbrainz:
                recommendation_provider_username = (
                    music_server_user.listenbrainz_username
                )
            else:
                recommendation_provider_username = music_server_user.lastfm_username

            if not recommendation_provider_username:
                raise ValueError(
                    f"{recommendation.provider.value} username not configured for user {music_server_user.username}"
                )

            resolved_blend_users: list[tuple[str, str]] | None = None

            if blend_users:
                resolved_blend_users = []

                for blend_username in blend_users:
                    music_server_user = get_music_server_user_by_username(
                        session=session,
                        username=blend_username,
                        provider=get_provider_enum(),
                    )

                    if not music_server_user:
                        raise ValueError(
                            f"Unable to find music server user '{blend_username}'"
                        )

                    if recommendation.provider == RecommendationProvider.listenbrainz:
                        blend_recommendation_provider_username = (
                            music_server_user.listenbrainz_username
                        )
                    else:
                        blend_recommendation_provider_username = (
                            music_server_user.lastfm_username
                        )

                    if not blend_recommendation_provider_username:
                        raise ValueError(
                            f"{recommendation.provider.value} username not configured for blend user '{blend_username}'"
                        )

                    blend_user_mapping = (
                        music_server_user.username,
                        blend_recommendation_provider_username,
                    )
                    resolved_blend_users.append(blend_user_mapping)

            logger.info(f"Processing {recommendation}")

            recommendation_session.status = RecommendationStatus.pending
            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            found_tracks, missing_tracks, provider_tracks = await get_recommendations(
                recommendation_provider=recommendation_provider,
                music_provider=provider,
                strategy=recommendation_session.strategy,
                num_recommendations=recommendation_session.requested_count,
                username=recommendation_provider_username,
                blend_users=resolved_blend_users,
            )
            all_tracks = found_tracks + missing_tracks

            logger.info(
                f"Found {len(found_tracks)} tracks and {len(missing_tracks)} missing tracks for user {recommendation_provider_username}"
            )
            if missing_tracks:
                downloaded_tracks, still_missing_tracks = await download_missing_tracks(
                    missing_tracks=[
                        track.to_external_track() for track in missing_tracks
                    ]
                )

                if downloaded_tracks:
                    logger.info(f"Downloaded {len(downloaded_tracks)} missing songs")

                    await provider.wait_for_rescan()

                    (
                        found_tracks_after_download,
                        missing_tracks_after_scan,
                    ) = await resolve_tracks(
                        provider=provider, tracks=downloaded_tracks
                    )

                    found_tracks, missing_tracks = reconcile_after_download(
                        found_tracks=found_tracks,
                        found_tracks_after_download=found_tracks_after_download,
                        missing_tracks=missing_tracks,
                        missing_tracks_after_download=still_missing_tracks,
                        missing_tracks_after_scan=missing_tracks_after_scan,
                        get_key=lambda t: (t.artist_name, t.track_name),
                    )

                    downloaded_provider_tracks = [
                        ProviderTrack(
                            id=resolved_track.provider_track_id,
                            track_name=resolved_track.track.track_name,
                            album_name=resolved_track.track.album_name,
                            album_id="",
                            musicbrainz_id="",
                            artists=[resolved_track.track.artist_name],
                            duration_ticks=0,
                            year=resolved_track.track.year,
                        )
                        for resolved_track in found_tracks_after_download
                        if resolved_track.provider_track_id
                    ]
                    provider_tracks.extend(downloaded_provider_tracks)
                    logger.debug(
                        f"Extended provider_tracks with {len(downloaded_provider_tracks)} newly downloaded tracks"
                    )

            finished_at = get_now()
            recommendation_session.status = RecommendationStatus.completed
            recommendation_session.finished_at = finished_at
            recommendation_session.duration_seconds = int(
                finished_at.timestamp() - started_at.timestamp()
            )
            recommendation_session.generated_count = len(found_tracks)
            recommendation_session.tracks = (
                build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(found_tracks),
                    type=RecommendationTrackType.matched,
                )
                + build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(missing_tracks),
                    type=RecommendationTrackType.missing,
                )
                + build_recommendation_session_tracks(
                    recommendation_session_id=recommendation_session_id,
                    names=format_recommendation_session_track_names(all_tracks),
                    type=RecommendationTrackType.total,
                )
            )

            update_recommendation_session(
                session=session, recommendation_session=recommendation_session
            )

            if not found_tracks:
                logger.info("No tracks found in provider for recommendations")
                return

            provider_track_ids = [track.id for track in provider_tracks]

            if not provider_track_ids:
                logger.info(
                    "No tracks from recommendations could be resolved to provider IDs"
                )
                return

            logger.info(
                f"Creating provider playlist with {len(provider_track_ids)} tracks"
            )

            decrypted_password = decrypt(music_server_user.password)

            playlist_id, provider_user_id = await provider.get_or_create_playlist(
                playlist_name=recommendation.playlist_name,
                is_public=recommendation.is_public,
                username=music_server_user.username,
                password=decrypted_password,
            )

            existing_tracks = await provider.get_playlist_songs(
                playlist_id=playlist_id,
                user_id=provider_user_id,
                username=music_server_user.username,
                password=decrypted_password,
            )

            if existing_tracks:
                await provider.delete_songs_from_playlist(
                    playlist_id=playlist_id,
                    entry_ids=[track.id for track in existing_tracks],
                    username=music_server_user.username,
                    password=decrypted_password,
                )

            await provider.add_songs_to_playlist(
                playlist_id=playlist_id,
                user_id=provider_user_id,
                track_ids=provider_track_ids,
                username=music_server_user.username,
                password=decrypted_password,
            )

        except Exception as e:
            if recommendation_session:
                finished_at = get_now()
                recommendation_session.status = RecommendationStatus.failed
                recommendation_session.finished_at = finished_at
                recommendation_session.duration_seconds = int(
                    finished_at.timestamp() - started_at.timestamp()
                )
                recommendation_session.error_message = truncate(
                    text=str(e), max_length=1024
                )
        finally:
            if recommendation_session:
                update_recommendation_session(
                    session=session, recommendation_session=recommendation_session
                )


async def generate_recommendations(
    provider: MusicPlaylistProvider,
    recommendation: Recommendation,
) -> dict[str, str]:
    """Get track recommendations for a user based on their listening history."""

    with get_isolated_session() as session:
        internal_recommendation = get_recommendation_by_id(
            session=session, recommendation_id=recommendation.id
        )

        if not internal_recommendation:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unable to find recommendation setting: {recommendation.id}",
            )

        started_at = get_now()
        recommendation_session = RecommendationSession(
            username=internal_recommendation.username,
            provider=internal_recommendation.provider,
            strategy=internal_recommendation.strategy,
            requested_count=internal_recommendation.requested_count,
            generated_count=0,
            blend_users=internal_recommendation.blend_users,
            started_at=started_at,
            finished_at=started_at,
            duration_seconds=0,
            status=RecommendationStatus.pending,
        )
        create_recommendation_session(
            session=session, recommendation_session=recommendation_session
        )

        logger.info(
            f"Scheduling background task to generate recommendations for user {internal_recommendation.username} with session ID {recommendation_session.id}"
        )
        await generate_recommendations_task(
            provider=provider,
            recommendation_session_id=recommendation_session.id,
            recommendation_id=internal_recommendation.id,
            blend_users=internal_recommendation.blend_users,
        )
        return {"id": str(recommendation_session.id)}
