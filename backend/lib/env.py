import os


def get_environment_variables() -> dict[str, str | bool | None]:
    return {
        "JELLYFIN_URL": os.getenv("JELLYFIN_URL", ""),
        "JELLYFIN_API_KEY": os.getenv("JELLYFIN_API_KEY", ""),
        "LASTFM_API_KEY": os.getenv("LASTFM_API_KEY", ""),
        "LASTFM_URL": os.getenv("LASTFM_URL", "https://ws.audioscrobbler.com/2.0/"),
        "DOWNLOAD_LIBRARY_NAME": os.getenv("DOWNLOAD_LIBRARY_NAME", "Downloads"),
        "DOWNLOAD_DIR": os.getenv("DOWNLOAD_DIR", "/downloads"),
        "AUTH_SECRET_KEY": os.getenv("AUTH_SECRET_KEY"),
        "NEXT_PUBLIC_URL": os.getenv("NEXT_PUBLIC_URL", "http://localhost:3000"),
        "DISCORD_WEBHOOK_URL": os.getenv("DISCORD_WEBHOOK_URL", ""),
        "DATABASE_USERNAME": os.getenv("DATABASE_USERNAME", "syllogi"),
        "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", "syllogi"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "localhost:5432"),
        "DATABASE_NAME": os.getenv("DATABASE_NAME", "syllogi"),
        "AUTHENTIK_CLIENT_ID": os.getenv("AUTHENTIK_CLIENT_ID", ""),
        "AUTHENTIK_SECRET": os.getenv("AUTHENTIK_SECRET", ""),
        "AUTHENTIK_ISSUER": os.getenv("AUTHENTIK_ISSUER", "").rstrip("/"),
        "IS_DEVELOPMENT": os.getenv("ENVIRONMENT", "production") == "development",
        "SLSKD_URL": os.getenv("SLSKD_URL", ""),
        "SLSKD_API_KEY": os.getenv("SLSKD_API_KEY", ""),
        "MUSICBRAINZ_URL": os.getenv("MUSICBRAINZ_URL", "https://musicbrainz.org/ws/2"),
        "MUSICBRAINZ_USER_AGENT": os.getenv(
            "MUSICBRAINZ_USER_AGENT",
            "syllogi/0.1.0 (https://github.com/jeraldlyh/syllogi)",
        ),
    }


def get_environment_variable(name: str, ignore_error=True) -> str | bool:
    variables = get_environment_variables()
    variable = variables.get(name, "")

    if not ignore_error and (
        variable is None or (isinstance(variable, str) and variable.strip() == "")
    ):
        raise ValueError(f"Environment variable '{name}' is required but not set.")
    return variable if variable is not None else ""


def is_oauth_configured() -> bool:
    variables = get_environment_variables()

    return bool(
        variables.get("AUTHENTIK_CLIENT_ID")
        and variables.get("AUTHENTIK_SECRET")
        and variables.get("AUTHENTIK_ISSUER")
    )


def is_slskd_configured() -> bool:
    variables = get_environment_variables()

    return bool(variables.get("SLSKD_URL") and variables.get("SLSKD_API_KEY"))
