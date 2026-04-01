<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="320" />
</p>

# syllogi

Sync playlists from external providers into Jellyfin using the music present in your library.

syllogi (Greek for "collection") imports playlist metadata from providers such as Spotify and YouTube, tries to match every track against audio already indexed by Jellyfin, and then creates or updates a Jellyfin playlist to mirror the source playlist as closely as possible. If a track is missing locally, it can optionally be downloaded with [yt-dlp](https://github.com/yt-dlp/yt-dlp), after which syllogi asks Jellyfin to rescan the download library and tries the match again.

## Features

- [x] Sync external playlists into Jellyfin
  - [x] Spotify
  - [x] YouTube
- [x] Optionally download missing tracks with `yt-dlp`
- [ ] Support notification messages
  - [x] Discord
- [ ] Allow tagging of downloaded tracks for easier future matching

## Requirements

- A running Jellyfin server
- A Jellyfin API key with permission to manage playlists
- A Jellyfin library that includes your local music
- `ffmpeg` installed if you want `yt-dlp` audio post-processing to work reliably

## Configuration

Provide configuration through environment variables.

| Name                            | Required | Description                                                                                              |
| ------------------------------- | -------- | -------------------------------------------------------------------------------------------------------- |
| `JELLYFIN_API_KEY`              | Yes      | Jellyfin API key for the target user with permission to create and manage playlists.                     |
| `JELLYFIN_BASE_URL`             | Yes      | Base URL of your Jellyfin server, for example `https://jellyfin.example.com` or `http://localhost:8096`. |
| `YOUTUBE_LIBRARY_NAME`          | No       | Name of the Jellyfin media folder that contains the yt-dlp downloads. Default: `Youtube`.                |
| `YOUTUBE_DOWNLOAD_DIR`          | No       | Filesystem path where downloaded tracks are written. Default: `/downloads`.                              |
| `DISABLE_MUSIC_VIDEO_DOWNLOADS` | No       | If `true`, the download search is biased toward lyric/audio-style uploads. Default: `true`.              |
| `DISCORD_WEBHOOK_URL`           | No       | Discord webhook URL for sync summary notifications. Leave unset to disable notifications.                |

## How it works

1. A playlist is read from a supported provider.
   - Spotify playlists are fetched through [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main).
   - YouTube playlists are fetched through `yt-dlp` metadata extraction.
2. syllogi converts each provider entry into a normalized internal track representation.
3. If missing tracks exist, syllogi can try to download them with `yt-dlp` into `YOUTUBE_DOWNLOAD_DIR`.
4. After downloading, syllogi requests a Jellyfin rescan of the media folder named by `YOUTUBE_LIBRARY_NAME`.
5. Newly indexed downloads are matched again.
6. syllogi compares the source playlist with the existing Jellyfin playlist and:
   - adds newly found tracks that are missing from the Jellyfin playlist
   - removes tracks that are no longer in the source playlist
   - leaves unchanged tracks as-is

## Matching behavior

Track resolution is based on metadata from the source playlist and the items available in Jellyfin. The search currently prioritizes title matching and then validates the result using metadata such as:

- artist
- album
- year
- duration

## Download behavior

When a track is missing from Jellyfin, syllogi can try to fetch it with `yt-dlp`.

- Downloads are written under `YOUTUBE_DOWNLOAD_DIR`
- Files are organized by artist and album, or under `Singles` when no album is available
- Audio is extracted to an Opus-based output through ffmpeg post-processing
- After download, Jellyfin is asked to refresh the configured download library so the track can be matched and added to the playlist in the subsequent run

Downloaded tracks are only useful for syncing once Jellyfin has indexed them successfully.

## Current limitations

- Matching is only as good as the metadata available from the provider and inside Jellyfin
- Jellyfin library refresh timing may vary depending on server size, so newly downloaded tracks may not appear immediately

## Credits

Special thanks to [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main), [yt-dlp](https://github.com/yt-dlp/yt-dlp), and [Jellyfin](https://github.com/jellyfin/jellyfin) for making this project possible.

## License

This project is licensed under the GPL 3.0 License. See [LICENSE](https://choosealicense.com/licenses/gpl-3.0/) for details.
