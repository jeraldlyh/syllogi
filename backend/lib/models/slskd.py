from dataclasses import dataclass

from lib.track import normalize


@dataclass
class SlskdSearchStatus:
    """A search result status from Soulseek endpoint.

    {{url}}/api/v0/searches/{search_id}
    """

    def __init__(
        self,
        id: str,
        search_text: str,
        state: str,
        token: int,
        file_count: int,
        locked_file_count: int,
        response_count: int,
        is_complete: bool,
        started_at: str,
        ended_at: str | None = None,
    ):
        self.id = id
        self.search_text = search_text
        self.state = state
        self.token = token
        self.file_count = file_count
        self.locked_file_count = locked_file_count
        self.response_count = response_count
        self.is_complete = is_complete
        self.started_at = started_at
        self.ended_at = ended_at

    def has_available_files(self) -> bool:
        return self.file_count > 0 and self.file_count > self.locked_file_count

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "id": self.id,
            "search_text": self.search_text,
            "state": self.state,
            "token": self.token,
            "file_count": self.file_count,
            "locked_file_count": self.locked_file_count,
            "response_count": self.response_count,
            "is_complete": self.is_complete,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


@dataclass
class SlskdSearchFile:
    """A file from Soulseek search results."""

    PREFERRED_EXTENSIONS = ["flac", "mp3", "opus"]

    def __init__(
        self,
        filename: str,
        size: int,
        is_locked: bool,
        length: int | None = None,
        sample_rate: int | None = None,
        bit_depth: int | None = None,
    ):
        self.filename = filename
        self.size = size
        self.is_locked = is_locked
        self.length = length
        self.sample_rate = sample_rate
        self.bit_depth = bit_depth

    def is_music_file(self) -> bool:
        return any(
            self.filename.lower().endswith(ext) for ext in self.PREFERRED_EXTENSIONS
        )

    def is_available(self) -> bool:
        return not self.is_locked and self.is_music_file()

    def is_matching(self, artist_name: str, track_name: str, duration: int) -> bool:
        normalized_filename = normalize(self.filename)

        if duration and self.length and abs(self.length - duration) > 10:
            return False

        return (
            normalize(track_name) in normalized_filename
            and normalize(artist_name) in normalized_filename
        )

    def to_dict(self) -> dict[str, str | int | bool | None]:
        return {
            "filename": self.filename,
            "size": self.size,
            "length": self.length,
            "sample_rate": self.sample_rate,
            "bit_depth": self.bit_depth,
            "is_locked": self.is_locked,
        }

    def __lt__(self, other) -> bool:
        return self.bit_depth < other.bit_depth


@dataclass
class SlskdSearchResult:
    """A search result from Soulseek endpoint.

    {{url}}/api/v0/searches/{search_id}/responses
    """

    def __init__(
        self,
        username: str,
        files: list[SlskdSearchFile],
        has_free_upload_slot: bool,
        locked_file_count: int,
        queue_length: int,
        token: int,
        upload_speed: int,
    ):
        self.username = username
        self.files = files
        self.has_free_upload_slot = has_free_upload_slot
        self.locked_file_count = locked_file_count
        self.queue_length = queue_length
        self.token = token
        self.upload_speed = upload_speed

    def to_dict(self) -> dict[str, str | int | bool | list[dict]]:
        return {
            "username": self.username,
            "files": [file.to_dict() for file in self.files],
            "has_free_upload_slot": self.has_free_upload_slot,
            "locked_file_count": self.locked_file_count,
            "queue_length": self.queue_length,
            "token": self.token,
            "upload_speed": self.upload_speed,
        }


@dataclass
class SlskdTrackCandidate:
    """A track candidate from Soulseek search results that matches the target track metadata."""

    def __init__(
        self,
        username: str,
        file: SlskdSearchFile,
    ):
        self.username = username
        self.file = file

    def to_dict(self) -> dict[str, str | int | bool | dict]:
        return {
            "username": self.username,
            "file": self.file.to_dict(),
        }


@dataclass
class SlskdDownloadFile:
    """A file from Soulseek downloads."""

    def __init__(
        self,
        id: str,
        username: str,
        direction: str,
        filename: str,
        size: int,
        start_offset: int,
        state: str,
        state_description: str,
        requested_at: str,
        enqueued_at: str,
        started_at: str,
        ended_at: str,
        bytes_transferred: int,
        average_speed: float,
        bytes_remaining: int,
        elapsed_time: str,
        percent_complete: int,
        remaining_time: str,
    ):
        self.id = id
        self.username = username
        self.direction = direction
        self.filename = filename
        self.size = size
        self.start_offset = start_offset
        self.state = state
        self.state_description = state_description
        self.requested_at = requested_at
        self.enqueued_at = enqueued_at
        self.started_at = started_at
        self.ended_at = ended_at
        self.bytes_transferred = bytes_transferred
        self.average_speed = average_speed
        self.bytes_remaining = bytes_remaining
        self.elapsed_time = elapsed_time
        self.percent_complete = percent_complete
        self.remaining_time = remaining_time

    def is_downloaded(self) -> bool:
        return self.state == "Completed, Succeeded" or self.percent_complete == 100

    def to_dict(self) -> dict[str, str | int | float]:
        return {
            "id": self.id,
            "username": self.username,
            "direction": self.direction,
            "filename": self.filename,
            "size": self.size,
            "start_offset": self.start_offset,
            "state": self.state,
            "state_description": self.state_description,
            "requested_at": self.requested_at,
            "enqueued_at": self.enqueued_at,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "bytes_transferred": self.bytes_transferred,
            "average_speed": self.average_speed,
            "bytes_remaining": self.bytes_remaining,
            "elapsed_time": self.elapsed_time,
            "percent_complete": self.percent_complete,
            "remaining_time": self.remaining_time,
        }


@dataclass
class SlskdDownloadDirectory:
    """A directory from Soulseek downloads."""

    def __init__(
        self,
        directory: str,
        file_count: int,
        files: list[SlskdDownloadFile],
    ):
        self.directory = directory
        self.file_count = file_count
        self.files = files

    def to_dict(self) -> dict[str, str | int | list[dict]]:
        return {
            "directory": self.directory,
            "file_count": self.file_count,
            "files": [file.to_dict() for file in self.files],
        }


@dataclass
class SlskdDownloadResult:
    """A download result from Soulseek endpoint after queuing a download.

    {{url}}/api/v0/transfers/downloads
    """

    def __init__(
        self,
        username: str,
        directories: list[SlskdDownloadDirectory],
    ):
        self.username = username
        self.directories = directories

    def to_dict(self) -> dict[str, str | list[dict]]:
        return {
            "username": self.username,
            "directories": [directory.to_dict() for directory in self.directories],
        }
