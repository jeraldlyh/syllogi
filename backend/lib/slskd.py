import asyncio
import glob
import logging
import os
import shutil
from pathlib import Path
from typing import Any

import httpx

from lib.models.slskd import (
    SlskdDownloadDirectory,
    SlskdDownloadFile,
    SlskdDownloadResult,
    SlskdSearchFile,
    SlskdSearchResult,
    SlskdSearchStatus,
    SlskdTrackCandidate,
)
from lib.env import get_environment_variable
from lib.musicbrainz import get_artist_alias
from lib.utils import find_downloaded_file, get_download_path, is_track_exists

logger = logging.getLogger(__name__)

SEARCH_POLL_INTERVAL = 10
SEARCH_MAX_RETRIES = 18

DOWNLOAD_RETRY_INTERVAL = 15
QUEUE_DOWNLOAD_MAX_RETRIES = 3
CHECK_DOWNLOAD_MAX_RETRIES = 40

TERMINAL_STATES = {
    "Completed, Cancelled",
    "Completed, TimedOut",
    "Completed, Errored",
    "Completed, Rejected",
}


async def _slskd(
    path: str,
    *,
    method: str = "GET",
    json: Any = None,
) -> Any:
    """Make a request to the slskd API."""

    url = get_environment_variable("SLSKD_URL", ignore_error=False)
    api_key = get_environment_variable("SLSKD_API_KEY", ignore_error=False)

    headers = {"X-API-Key": str(api_key)}

    async with httpx.AsyncClient(verify=False, timeout=30) as client:
        response = await client.request(
            method=method, url=str(url).rstrip("/") + path, headers=headers, json=json
        )
        response.raise_for_status()

        if response.content:
            return response.json()
        return None


async def _search_track(search_text: str) -> str:
    """Initiate a search on slskd. Returns the search ID."""

    result = await _slskd(
        "/api/v0/searches", method="POST", json={"searchText": search_text}
    )

    return result["id"]


async def _search_track_status(search_id: str) -> SlskdSearchStatus:
    """Fetch the status of a search on slskd."""

    result = await _slskd(f"/api/v0/searches/{search_id}")

    return SlskdSearchStatus(
        id=result["id"],
        search_text=result["searchText"],
        state=result["state"],
        token=result["token"],
        file_count=result["fileCount"],
        locked_file_count=result["lockedFileCount"],
        response_count=result["responseCount"],
        is_complete=result["isComplete"],
        started_at=result["startedAt"],
        ended_at=result.get("endedAt"),
    )


async def _is_search_completed(search_id: str) -> bool:
    """Poll until search is complete. Returns True if available files were found."""

    for attempt in range(1, SEARCH_MAX_RETRIES + 1):
        search_status = await _search_track_status(search_id)

        if search_status.is_complete:
            return True

        logger.warning(
            f"[{attempt}/{SEARCH_MAX_RETRIES}] Search {search_id} not complete yet. State: {search_status.state}. "
        )
        await asyncio.sleep(SEARCH_POLL_INTERVAL)
    return False


async def _get_search_results(search_id: str) -> list[SlskdSearchResult]:
    """Fetch slskd search results for a completed search."""

    result = await _slskd(f"/api/v0/searches/{search_id}/responses")

    return [
        SlskdSearchResult(
            username=res.get("username", ""),
            files=[
                SlskdSearchFile(
                    filename=file.get("filename"),
                    size=file.get("size"),
                    is_locked=file.get("isLocked"),
                    length=file.get("length"),
                    sample_rate=file.get("sampleRate"),
                    bit_depth=file.get("bitDepth"),
                )
                for file in res.get("files")
            ],
            has_free_upload_slot=res.get("hasFreeUploadSlot"),
            locked_file_count=res.get("lockedFileCount"),
            queue_length=res.get("queueLength"),
            token=res.get("token"),
            upload_speed=res.get("uploadSpeed"),
        )
        for res in result
    ]


async def _queue_download(username: str, filename: str, size: int) -> bool:
    """Queue a download on slskd.

    Returns True if the download was successfully queued, False otherwise.
    """

    for attempt in range(1, QUEUE_DOWNLOAD_MAX_RETRIES + 1):
        try:
            logger.info(
                f"[{attempt}/{QUEUE_DOWNLOAD_MAX_RETRIES}] Queueing download for {filename} from user {username}"
            )

            await _slskd(
                f"/api/v0/transfers/downloads/{username}",
                method="POST",
                json=[{"filename": filename, "size": size}],
            )
            return True
        except Exception as e:
            logger.error(
                f"[{attempt}/{QUEUE_DOWNLOAD_MAX_RETRIES}] Failed to queue download for {filename}: {e}"
            )

        await asyncio.sleep(DOWNLOAD_RETRY_INTERVAL)
    return False


async def _get_downloads() -> list[SlskdDownloadResult]:
    """Fetch current downloads from slskd."""

    result = await _slskd("/api/v0/transfers/downloads")

    downloads: list[SlskdDownloadResult] = []

    for entry in result:
        directories = entry.get("directories")
        slskd_directories: list[SlskdDownloadDirectory] = []

        for directory in directories:
            files = directory.get("files")
            slskd_files: list[SlskdDownloadFile] = []

            for file in files:
                slskd_files.append(
                    SlskdDownloadFile(
                        id=file.get("id"),
                        username=file.get("username"),
                        direction=file.get("direction"),
                        filename=file.get("filename"),
                        size=file.get("size"),
                        start_offset=file.get("startOffset"),
                        state=file.get("state"),
                        state_description=file.get("stateDescription"),
                        requested_at=file.get("requestedAt"),
                        enqueued_at=file.get("enqueuedAt"),
                        started_at=file.get("startedAt"),
                        ended_at=file.get("endedAt"),
                        bytes_transferred=file.get("bytesTransferred"),
                        average_speed=file.get("averageSpeed"),
                        bytes_remaining=file.get("bytesRemaining"),
                        elapsed_time=file.get("elapsedTime"),
                        percent_complete=file.get("percentComplete"),
                        remaining_time=file.get("remainingTime"),
                    )
                )
            slskd_directories.append(
                SlskdDownloadDirectory(
                    directory=directory.get("directory"),
                    file_count=directory.get("fileCount"),
                    files=slskd_files,
                )
            )
        downloads.append(
            SlskdDownloadResult(
                username=entry.get("username"),
                directories=slskd_directories,
            )
        )
    return downloads


async def _is_download_completed(username: str, filename: str) -> bool:
    """Poll until the download completes or fails.

    Returns True if the download completed successfully, False otherwise.
    """

    for attempt in range(1, CHECK_DOWNLOAD_MAX_RETRIES + 1):
        try:
            downloaded_file = await _get_downloaded_file(username, filename)

            if downloaded_file:
                if downloaded_file.is_downloaded():
                    return True

                if downloaded_file.state in TERMINAL_STATES:
                    return False
            logger.warning(
                f"[{attempt}/{CHECK_DOWNLOAD_MAX_RETRIES}] Download for {filename} from user {username} not completed yet. State: {downloaded_file.state if downloaded_file else 'N/A'}."
            )
        except Exception as e:
            logger.error(f"Failed to poll download status: {e}")

        await asyncio.sleep(DOWNLOAD_RETRY_INTERVAL)
    return False


async def _get_downloaded_file(
    username: str, filename: str
) -> SlskdDownloadFile | None:
    """Fetch the downloaded file info from slskd after completion."""

    try:
        downloads = await _get_downloads()

        for download in downloads:
            if download.username != username:
                continue

            for directory in download.directories:
                for file in directory.files:
                    if file.filename == filename:
                        return file
    except Exception as e:
        logger.warning(f"Error fetching downloaded file info: {e}")

    return None


def _rename_slskd_download(
    remote_filename: str,
    artist_name: str,
    track_name: str,
    album_name: str,
) -> bool:
    """Move a completed slskd download to the standard download path.

    Searches for the downloaded file by its basename within DOWNLOAD_DIR and
    moves it to the path produced by get_download_path(), mirroring the format
    used by the YouTube downloader:
      {DOWNLOAD_DIR}/{artist}/{album}/{track}.{ext}
    or
      {DOWNLOAD_DIR}/{artist}/Singles/{track}.{ext}

    Returns True if the file exists at the correct location after the operation.
    """
    if is_track_exists(
        artist_name=artist_name, track_name=track_name, album_name=album_name
    ):
        logger.info(
            f"slskd file already at correct location for: {artist_name} - {track_name}"
        )
        return True

    local_path = find_downloaded_file(remote_filename)

    if not local_path:
        logger.warning(f"Could not locate downloaded slskd file: {remote_filename}")
        return False

    ext = Path(local_path).suffix
    target_path = get_download_path(artist_name, track_name, album_name) + ext

    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    shutil.move(local_path, target_path)
    logger.info(f"Renamed slskd download: {local_path} -> {target_path}")

    return is_track_exists(artist_name, track_name, album_name)


def _get_best_entry(
    entries: list[SlskdSearchResult],
    artist_name: str,
    track_name: str,
    duration: int,
) -> SlskdTrackCandidate | None:
    """Get the best entry from a list of slskd search results based on heuristics."""

    candidates: list[SlskdTrackCandidate] = []

    for entry in entries:
        if not entry.has_free_upload_slot:
            continue

        for file in entry.files:
            if file.is_available() and file.is_matching(
                artist_name=artist_name,
                track_name=track_name,
                duration=duration,
            ):
                candidates.append(
                    SlskdTrackCandidate(username=entry.username, file=file)
                )

    if candidates:
        return max(candidates, key=lambda e: e.file.bit_depth or 0)
    return None


async def _delete_search(search_id: str) -> None:
    """Delete a completed/failed search from slskd."""

    try:
        await _slskd(f"/api/v0/searches/{search_id}", method="DELETE")
    except Exception as e:
        logger.debug(f"Failed to delete search {search_id}: {e}")


async def _delete_download(user_id: str, file_id: str) -> None:
    """Delete completed/failed downloads from slskd."""

    try:
        await _slskd(
            f"/api/v0/transfers/downloads/{user_id}/{file_id}?remove=true",
            method="DELETE",
        )
    except Exception as e:
        logger.error(
            f"Failed to delete download for user {user_id} and file {file_id}: {e}"
        )


async def download_track_slskd(
    artist_name: str,
    track_name: str,
    album_name: str = "",
    duration: int = 0,
) -> bool:
    """Search for a track on Soulseek via slskd and download it.

    Returns True if the download completed successfully, False otherwise.
    """

    search_id: str | None = None
    downloaded_file: SlskdDownloadFile | None = None

    search_query = f"{artist_name} {track_name}"

    try:
        search_id = await _search_track(search_text=search_query)

        if not await _is_search_completed(search_id=search_id):
            return False

        results = await _get_search_results(search_id)

        if not results:
            await _delete_search(search_id)

            artist_alias = await get_artist_alias(artist_name)

            if not artist_alias or artist_alias.lower() == artist_name.lower():
                logger.warning(f"No artist alias found for {artist_name}")
                return False

            search_query = f"{artist_alias} {track_name}"

            logger.info(
                f"Retrying search with artist alias {artist_alias} for artist {artist_name!r}"
            )

            search_id = await _search_track(search_text=search_query)

            if not await _is_search_completed(search_id=search_id):
                return False

            results = await _get_search_results(search_id)

        best_entry = _get_best_entry(
            entries=results,
            artist_name=artist_name,
            track_name=track_name,
            duration=duration,
        )

        if not best_entry:
            logger.warning(f"No suitable file found for: {search_query}")
            return False

        if not await _queue_download(
            username=best_entry.username,
            filename=best_entry.file.filename,
            size=best_entry.file.size,
        ):
            return False

        is_download_completed = await _is_download_completed(
            best_entry.username, best_entry.file.filename
        )

        downloaded_file = await _get_downloaded_file(
            best_entry.username, best_entry.file.filename
        )

        if is_download_completed:
            rename_success = _rename_slskd_download(
                remote_filename=best_entry.file.filename,
                artist_name=artist_name,
                track_name=track_name,
                album_name=album_name,
            )

            if not rename_success:
                logger.error(
                    f"Download succeeded but failed to move file to standard path for: {search_query}"
                )
                return False

        return is_download_completed
    except Exception as e:
        logger.error(f"Failed to download '{search_query}': {e}")

        return False
    finally:
        if search_id:
            await _delete_search(search_id)

        if downloaded_file:
            await _delete_download(downloaded_file.username, downloaded_file.id)
