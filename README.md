<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="160" />
</p>

# syllogi

**syllogi** is a self-hosted automation tool that keeps your [Jellyfin] or [Navidrome] music library in sync with external playlists from Spotify and YouTube.

It matches tracks against your indexed audio, automatically downloads missing tracks via [yt-dlp] or [slskd], generates personalized recommendations based on your listening history, and lets you browse trending charts, all from a single dashboard.

## Documentation

Full documentation lives at **[docs.syllogi.dev](https://docs.syllogi.dev)**:

- [Quick Start](https://docs.syllogi.dev/docs/quick-start) - run the stack with Docker Compose.
- [Features](https://docs.syllogi.dev/docs/features) - how sync, downloads, recommendations, charts and library management work.
- [Configuration](https://docs.syllogi.dev/docs/configuration) - every environment variable, plus Authentik SSO.

## Features

- **[Playlist Sync](https://docs.syllogi.dev/docs/features/playlist-sync)** - mirrors public Spotify and YouTube playlists into your music server on a cron schedule, with a per-run breakdown of what was added, removed, missing or downloaded.
- **[Downloads](https://docs.syllogi.dev/docs/features/downloads)** - fetches tracks missing from your library via [slskd] or [yt-dlp] and triggers a library rescan.
- **[Recommendations](https://docs.syllogi.dev/docs/features/recommendations)** - builds a daily playlist from your [Last.fm] scrobbles using one of four seeding strategies.
- **[Charts](https://docs.syllogi.dev/docs/features/charts)** - browses globally trending tracks and queues any of them for download.
- **[Library](https://docs.syllogi.dev/docs/features/library)** - browses and retags the audio files in your download directory from the dashboard.

## Quick Start

1. Copy the example compose file:

   ```bash
   cp docker-compose.example.yml docker-compose.yml
   ```

2. Fill in the required environment variables (see [Configuration](https://docs.syllogi.dev/docs/configuration)).

3. Start the stack:

   ```bash
   docker compose up -d
   ```

4. Open the dashboard at `http://localhost:8000` and register your first account.

5. Add a playlist, set a sync schedule, setup recommendations, and **syllogi** will take it from there.

[Jellyfin]: https://github.com/jellyfin/jellyfin
[Navidrome]: https://github.com/navidrome/navidrome
[yt-dlp]: https://github.com/yt-dlp/yt-dlp
[slskd]: https://github.com/slskd/slskd
[Last.fm]: https://www.last.fm/
