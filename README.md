<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="320" />
</p>

# syllogi

Sync playlists from external providers into Jellyfin using the music present in your library.

syllogi (Greek for "collection") imports playlist metadata from providers such as Spotify and YouTube, tries to match every track against audio already indexed by Jellyfin, and then creates or updates a Jellyfin playlist to mirror the source playlist as closely as possible. If a track is missing locally, it can optionally be downloaded with [yt-dlp](https://github.com/yt-dlp/yt-dlp), after which syllogi asks Jellyfin to rescan the download library and tries the match again.

## Features

### Sync

- Create and manage multiple playlists with different sources and sync cron schedules.
- Download missing tracks from YouTube with `yt-dlp` and automatically add them to Jellyfin.

### Authentication

- Basic username and password authentication for the web UI>
- OAuth-based SSO authentication with external providers - [Authentik](https://goauthentik.io).

### Notifications

- Sync session summary messages with Discord webhooks.

## Requirements

- A running Jellyfin server with an API key that has permission to manage playlists.
- A Jellyfin library that includes your local music.
- `docker` and `docker-compose`.

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

5. Add a playlist, set a sync schedule, and syllogi will take it from there.

## Configuration

All configuration is supplied through environment variables on the `syllogi` container.

### Required

| Name                | Description                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| `JELLYFIN_API_KEY`  | Jellyfin API key for the target user with permission to create and manage playlists.              |
| `JELLYFIN_BASE_URL` | Base URL of your Jellyfin server, e.g. `https://jellyfin.example.com` or `http://localhost:8096`. |
| `DATABASE_URL`      | PostgreSQL host and port, e.g. `syllogi-postgres:5432`.                                           |
| `DATABASE_USERNAME` | PostgreSQL username.                                                                              |
| `DATABASE_PASSWORD` | PostgreSQL password.                                                                              |
| `DATABASE_NAME`     | PostgreSQL database name.                                                                         |
| `NEXT_PUBLIC_URL`   | Public URL of the syllogi web UI, e.g. `http://localhost:8000`. Used for OAuth redirect URIs.     |

### Optional

| Name                   | Default         | Description                                                                         |
| ---------------------- | --------------- | ----------------------------------------------------------------------------------- |
| `YOUTUBE_LIBRARY_NAME` | `Youtube`       | Name of the Jellyfin media folder that contains the yt-dlp downloads.               |
| `YOUTUBE_DOWNLOAD_DIR` | `/downloads`    | Filesystem path inside the container where downloaded tracks are written.           |
| `DISCORD_WEBHOOK_URL`  | _(unset)_       | Discord webhook URL for sync summary notifications. Leave unset to disable.         |
| `SECRET_KEY`           | _(default key)_ | Secret used to sign JWT session tokens. Set to a long random string in production.  |
| `LOG_LEVEL`            | `INFO`          | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).                         |
| `AUTHENTIK_CLIENT_ID`  | _(unset)_       | Authentik OAuth application client ID. Required only if you want SSO via Authentik. |
| `AUTHENTIK_SECRET`     | _(unset)_       | Authentik OAuth application client secret.                                          |
| `AUTHENTIK_ISSUER`     | _(unset)_       | Authentik OIDC issuer URL, e.g. `https://auth.example.com/application/o/syllogi/`.  |
| `TZ`                   | _(unset)_       | Container timezone, e.g. `Asia/Singapore`. Affects cron scheduling.                 |
| `ENVIRONMENT`          | `production`    | Set to `production` to use the built Next.js output.                                |

## OIDC Setup with Authentik

This section walks you through creating an OIDC provider in [Authentik](https://goauthentik.io) and wiring it up to syllogi.

### 1. Create an OIDC Provider in Authentik

1. Log in to your Authentik admin interface (e.g. `https://auth.example.com/if/admin/`).
2. Click **Create** and select **OAuth2/OpenID Connect Provider**.
3. Fill in the following fields:
   - **Name** - e.g. `syllogi`
   - **Authorization flow** - select your desired authorization flow (e.g. `default-provider-authorization-explicit-consent`).
   - **Client type** - `Confidential`
   - **Redirect URIs/Origins** - add the callback URL:
     ```
     <public-url-of-syllogi>/oauth/callback # i.e. https://syllogi.com/oauth/callback
     ```
4. Leave all other settings at their defaults and click **Save**.
5. On the provider detail page, note down the **Client ID** and **Client Secret**

### 2. Create an Authentik Application

1. Navigate to **Applications → Applications** in the sidebar.
2. Click **Create** and fill in:
   - **Name** - e.g. `syllogi`
   - **Slug** - e.g. `syllogi`
   - **Provider** - select the provider you just created.
3. Click **Save**.

### 3. Retrieve the OIDC Issuer URL

1. Go back to **Applications → Providers** and open the provider you created.
2. Scroll down to the **OpenID Configuration** section.
3. Copy the **OpenID Configuration URL** - it will look like:
   ```
   https://auth.example.com/application/o/syllogi/
   ```
   This is your issuer URL (`AUTHENTIK_ISSUER`).

### 4. Configure syllogi

Set the following environment variables on the `syllogi` container in your `docker-compose.yml`:

```yaml
environment:
  AUTHENTIK_CLIENT_ID: "<client-id-from-step-1>"
  AUTHENTIK_SECRET: "<client-secret-from-step-1>"
  AUTHENTIK_ISSUER: "<issuer-url-from-step-3>"
  NEXT_PUBLIC_URL: "<public-url-of-syllogi>"
```

---

## How it works

1. A playlist is read from a supported provider.
   - Spotify playlists are fetched through [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main).
   - YouTube playlists are fetched through `yt-dlp` metadata extraction.
2. syllogi converts each provider entry into a normalized internal track representation.
3. Each track is searched in the Jellyfin library using title, artist, album, year, and duration.
4. The difference between the source playlist and the existing Jellyfin playlist is computed:
   - **Added** - tracks in the source that are not yet in Jellyfin.
   - **Removed** - tracks in Jellyfin that are no longer in the source.
   - **Unchanged** - tracks present in both.
5. If missing tracks exist and `enable_download` is set, syllogi tries to fetch them with `yt-dlp`.
6. After downloading, Jellyfin is asked to refresh the configured download library and the newly indexed tracks are matched again.
7. The Jellyfin playlist is updated and the playlist thumbnail is synced from the source.
8. A sync session record is saved to the database with a full per-track breakdown.
9. If `DISCORD_WEBHOOK_URL` is set, a summary embed is posted to the webhook.

> Current limitations
>
> - Matching of tracks between source and provider is only as good as the metadata available from the provider and inside Jellyfin
> - Jellyfin library refresh timing may vary depending on server size, so newly downloaded tracks may not appear immediately after a single sync run
> - OAuth state is stored in-memory, hence a container restart will invalidate any in-flight OAuth flows

## Credits

Special thanks to [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main), [yt-dlp](https://github.com/yt-dlp/yt-dlp), and [Jellyfin](https://github.com/jellyfin/jellyfin) for making this project possible.

## License

This project is licensed under the GPL 3.0 License. See [LICENSE](https://choosealicense.com/licenses/gpl-3.0/) for details.
