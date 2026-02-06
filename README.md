<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="320" />
</p>

# syllogi

Import Spotify playlists into Jellyfin from your existing library.

syllogi (Greek for "collection") is an automation workflow that imports Spotify playlists into Jellyfin by attempting to replicate a one-to-one playlist using only audio files that already exist on your server. Unmatched tracks are skipped and summarized.

## Features

- [x] Build or update Jellyfin playlists from Spotify playlists
- [] Notification report of matched and unmatched tracks
  - [x] Discord

## Requirements

- A running Jellyfin server and an API key with permission to manage playlists

## Configuration

Provide credentials and connection details via environment variables or a config file.

| Name                | Required | Description                                                                                                                         |
| ------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| JELLYFIN_API_KEY    | Yes      | Jellyfin API key for the target user with permission to create and manage playlists. Generate it in Jellyfin: Dashboard → API Keys. |
| JELLYFIN_BASE_URL   | Yes      | Base URL of your Jellyfin server, e.g. https://jellyfin.example.com or http://localhost:8096.                                       |
| DISCORD_WEBHOOK_URL | No       | Discord Webhook URL to post the match/unmatched summary report. Leave unset to disable notifications.                               |

## How it works

1. Read a Spotify playlist with [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main) and fetch playlist metadata without requiring any credentials.
2. Match each track against your Jellyfin library by tags (artist name and title).
3. Syncs Jellyfin playlist that exists in Spotify playlist and containing only the tracks found locally.

## Credits

Special thanks to [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main) and [Jellyfin](https://github.com/jellyfin/jellyfin) for making this entire project possible!

## License

This project is licensed under the GPL 3.0 License. See [LICENSE](https://choosealicense.com/licenses/gpl-3.0/) for details.
