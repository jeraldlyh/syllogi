<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="320" />
</p>

# syllogi

**syllogi** mirrors external playlists into Jellyfin by matching tracks against your indexed audio. Missing tracks can optionally be downloaded with [yt-dlp] or [slskd].

Supported playlist providers:

| Provider    | Requirements                                                       |
| ----------- | ------------------------------------------------------------------ |
| **Spotify** | No API key or account needed, public playlists only, via [SpotAPI] |
| **YouTube** | No API key needed, public playlists only, via [yt-dlp]             |

> [!WARNING]
>
> - Matching depends on metadata quality from the provider and Jellyfin.
> - Jellyfin library refresh timing can delay newly downloaded tracks.
> - OAuth state is stored in-memory, so a restart invalidates in-flight OAuth flows.

## Quick Links

- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Credits](#credits)

---

## Features

### Playlist Sync

Mirrors external Spotify or YouTube playlists into Jellyfin. Each sync run diffs the source playlist against your Jellyfin library and produces a per-run breakdown:

| Column     | Description                                          |
| ---------- | ---------------------------------------------------- |
| Total      | Total tracks in the source playlist                  |
| New        | Tracks added to the Jellyfin playlist this run       |
| Removed    | Tracks removed because they left the source playlist |
| Missing    | Tracks not found in the library and not downloaded   |
| Downloaded | Tracks that were downloaded and added this run       |

Each playlist requires a **Jellyfin username** (the exact username of the Jellyfin account that will own the playlist) and a **cron schedule**.

### Downloads

Missing tracks are downloaded automatically via the following providers:

1. [slskd] if `SLSKD_URL` and `SLSKD_API_KEY` are set.
2. [yt-dlp] as a fallback.

Downloaded files are placed in `DOWNLOAD_DIR` and the Jellyfin library is rescanned immediately after.

### Recommendations

Generates a playlist named `Daily Recommendations` in Jellyfin based on your [Last.fm] scrobble history (requires `LASTFM_API_KEY`). The existing playlist is replaced with fresh recommendations daily. Supports three strategies:

| Strategy        | Description                                                  |
| --------------- | ------------------------------------------------------------ |
| `top_tracks`    | Seeds from your all-time Last.fm top tracks (6-month window) |
| `recent_tracks` | Seeds from your recently scrobbled tracks                    |
| `mixed`         | 50% top tracks + 50% recent tracks                           |

Each recommendation rule requires a **Jellyfin username**, a **Last.fm username**, the desired strategy, a track count, and a cron schedule.

### Charts

Browse Last.fm globally trending tracks, and tracks can be queued for download directly from the Charts tab. The download activity log on the dashboard tracks the status of all in-progress and completed downloads.

## Quick Start

1. Copy the example compose file:

   ```bash
   cp docker-compose.example.yml docker-compose.yml
   ```

2. Fill in the required environment variables (see [Configuration](#configuration) below).

3. Start the stack:

   ```bash
   docker compose up -d
   ```

4. Open the dashboard at `http://localhost:8000` and register your first account.

5. Add a playlist, set a sync schedule, setup recommendations, and **syllogi** will take it from there.

### Requirements

- A running Jellyfin server with an API key that has permission to manage playlists.
- A Jellyfin library that includes your local music.
- Docker and Docker Compose.

### Building from source

If you want to build the image locally instead of using the pre-built one, clone the repository **with submodules** (the Spotify client is a git submodule):

```bash
git clone --recurse-submodules https://github.com/jeraldlyh/syllogi.git
cd syllogi
```

If you already cloned without `--recurse-submodules`, run:

```bash
git submodule update --init --recursive
```

Then use the development compose file which builds from source with hot-reload:

```bash
docker compose up -d
```

---

## Configuration

All configuration is supplied through environment variables on the `syllogi` container.

### Environment variables

#### Required

| Name                | Description                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| `JELLYFIN_API_KEY`  | Jellyfin API key for the target user with permission to create and manage playlists.              |
| `JELLYFIN_URL`      | Base URL of your Jellyfin server, e.g. `https://jellyfin.example.com` or `http://localhost:8096`. |
| `DATABASE_URL`      | PostgreSQL host and port, e.g. `syllogi-postgres:5432`.                                           |
| `DATABASE_USERNAME` | PostgreSQL username.                                                                              |
| `DATABASE_PASSWORD` | PostgreSQL password.                                                                              |
| `DATABASE_NAME`     | PostgreSQL database name.                                                                         |
| `NEXT_PUBLIC_URL`   | Public URL of the syllogi web UI, e.g. `http://localhost:8000`. Used for OAuth redirect URIs.     |
| `AUTH_SECRET_KEY`   | Secret used to sign JWT session tokens. Set to a long random string in production.                |

#### Optional

| Name                     | Default                                                | Description                                                                                                                       |
| ------------------------ | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| `DOWNLOAD_LIBRARY_NAME`  | `Downloads`                                            | Name of the Jellyfin media folder that contains the yt-dlp downloads.                                                             |
| `DOWNLOAD_DIR`           | `/downloads`                                           | Filesystem path inside the container where downloaded tracks are written. This path should also match Jellyfin's library path.    |
| `DISCORD_WEBHOOK_URL`    | _(unset)_                                              | Discord webhook URL for sync summary notifications. Leave unset to disable.                                                       |
| `LOG_LEVEL`              | `INFO`                                                 | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).                                                                       |
| `AUTHENTIK_CLIENT_ID`    | _(unset)_                                              | Authentik OAuth application client ID. Required only if you want SSO via Authentik.                                               |
| `AUTHENTIK_SECRET`       | _(unset)_                                              | Authentik OAuth application client secret.                                                                                        |
| `AUTHENTIK_ISSUER`       | _(unset)_                                              | Authentik OIDC issuer URL, e.g. `https://auth.example.com/application/o/syllogi/`.                                                |
| `TZ`                     | _(unset)_                                              | Container timezone, e.g. `Asia/Singapore`. Affects cron scheduling.                                                               |
| `ENVIRONMENT`            | `production`                                           | Set to `development` to enable debug features (raw API response dumps). Defaults to `production`.                                 |
| `MUSICBRAINZ_URL`        | `https://musicbrainz.org/ws/2`                         | Base URL for MusicBrainz API.                                                                                                     |
| `MUSICBRAINZ_USER_AGENT` | `syllogi/0.1.0 (https://github.com/jeraldlyh/syllogi)` | User agent string for MusicBrainz API requests.                                                                                   |
| `LASTFM_API_KEY`         | _(unset)_                                              | Last.fm API key for generating recommendations based on your scrobbles. See [Last.fm API documentation](https://www.last.fm/api). |
| `LASTFM_URL`             | `https://ws.audioscrobbler.com/2.0`                    | Base URL for Last.fm API.                                                                                                         |
| `SLSKD_URL`              | _(unset)_                                              | Base URL for SLSKD API.                                                                                                           |
| `SLSKD_API_KEY`          | _(unset)_                                              | API key for SLSKD for downloading audio when tracks are missing from library.                                                     |

### Authentik OIDC

Use Authentik for SSO by creating an OIDC provider and setting the variables below.

1. Create an OAuth2/OIDC provider in Authentik with:
   - **Client type**: `Confidential`
   - **Redirect URI**: `<public-url-of-syllogi>/oauth/callback`
2. Create an Authentik application and attach the provider.
3. Copy the **Client ID**, **Client Secret**, and **OpenID Configuration URL** (issuer).
4. Set these environment variables:

```yaml
environment:
  AUTHENTIK_CLIENT_ID: "<client-id>"
  AUTHENTIK_SECRET: "<client-secret>"
  AUTHENTIK_ISSUER: "<issuer-url>"
  NEXT_PUBLIC_URL: "<public-url-of-syllogi>"
```

---

## Credits

Special thanks to the following projects for making **syllogi** possible:

- [SpotAPI]
- [yt-dlp]
- [Jellyfin]
- [Last.fm]
- [slskd]

[SpotAPI]: https://github.com/Aran404/SpotAPI/tree/main
[yt-dlp]: https://github.com/yt-dlp/yt-dlp
[Jellyfin]: https://github.com/jellyfin/jellyfin
[Last.fm]: https://www.last.fm/
[slskd]: https://github.com/slskd/slskd
