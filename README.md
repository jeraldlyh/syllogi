<p align="center">
  <img src="assets/icon.png" alt="syllogi logo" width="320" />
</p>

# syllogi

**syllogi** mirrors external playlists into Jellyfin by matching tracks against your indexed audio. Missing tracks can optionally be downloaded with [yt-dlp](https://github.com/yt-dlp/yt-dlp).

> ⚠️ **Current limitations**
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

- Generates and maintains playlists in Jellyfin based on an external playlist.
  - Matches tracks against your Jellyfin library using audio metadata.
- Downloads missing tracks and re-scans the download library.
- Generates playlist with track recommendations based on your scrobbles with Last.fm.

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

<details>
<summary><strong>Requirements</strong></summary>

- A running Jellyfin server with an API key that has permission to manage playlists.
- A Jellyfin library that includes your local music.
- Docker and Docker Compose.

</details>

---

## Configuration

All configuration is supplied through environment variables on the `syllogi` container.

<details>
<summary><strong>Environment variables</strong></summary>

#### Required

| Name                | Description                                                                                       |
| ------------------- | ------------------------------------------------------------------------------------------------- |
| `JELLYFIN_API_KEY`  | Jellyfin API key for the target user with permission to create and manage playlists.              |
| `JELLYFIN_BASE_URL` | Base URL of your Jellyfin server, e.g. `https://jellyfin.example.com` or `http://localhost:8096`. |
| `DATABASE_URL`      | PostgreSQL host and port, e.g. `syllogi-postgres:5432`.                                           |
| `DATABASE_USERNAME` | PostgreSQL username.                                                                              |
| `DATABASE_PASSWORD` | PostgreSQL password.                                                                              |
| `DATABASE_NAME`     | PostgreSQL database name.                                                                         |
| `NEXT_PUBLIC_URL`   | Public URL of the syllogi web UI, e.g. `http://localhost:8000`. Used for OAuth redirect URIs.     |

#### Optional

| Name                    | Default         | Description                                                                         |
| ----------------------- | --------------- | ----------------------------------------------------------------------------------- |
| `DOWNLOAD_LIBRARY_NAME` | `Downloads`     | Name of the Jellyfin media folder that contains the yt-dlp downloads.               |
| `DOWNLOAD_DIR`          | `/downloads`    | Filesystem path inside the container where downloaded tracks are written.           |
| `DISCORD_WEBHOOK_URL`   | _(unset)_       | Discord webhook URL for sync summary notifications. Leave unset to disable.         |
| `SECRET_KEY`            | _(default key)_ | Secret used to sign JWT session tokens. Set to a long random string in production.  |
| `LOG_LEVEL`             | `INFO`          | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`).                         |
| `AUTHENTIK_CLIENT_ID`   | _(unset)_       | Authentik OAuth application client ID. Required only if you want SSO via Authentik. |
| `AUTHENTIK_SECRET`      | _(unset)_       | Authentik OAuth application client secret.                                          |
| `AUTHENTIK_ISSUER`      | _(unset)_       | Authentik OIDC issuer URL, e.g. `https://auth.example.com/application/o/syllogi/`.  |
| `TZ`                    | _(unset)_       | Container timezone, e.g. `Asia/Singapore`. Affects cron scheduling.                 |
| `ENVIRONMENT`           | `production`    | Set to `production` to use the built Next.js output.                                |

</details>

<details>
<summary><strong>Authentik OIDC</strong></summary>

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

</details>

---

## Credits

Special thanks to the following projects for making **syllogi** possible:

- [SpotAPI](https://github.com/Aran404/SpotAPI/tree/main)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [Jellyfin](https://github.com/jellyfin/jellyfin)
- [Last.fm](https://www.last.fm/)
