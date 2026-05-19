import httpx

from typing import Any

from fastapi import HTTPException, status

from lib.env import get_environment_variable


def _get_authentik_config() -> dict:
    """Validate that Authentik env vars are set and return them."""

    authentik_client_id = get_environment_variable("AUTHENTIK_CLIENT_ID")
    authentik_secret = get_environment_variable("AUTHENTIK_SECRET")
    authentik_issuer = get_environment_variable("AUTHENTIK_ISSUER")

    auth_url = authentik_issuer.split("application")[0].rstrip("/")
    return {
        "client_id": authentik_client_id,
        "client_secret": authentik_secret,
        "issuer": authentik_issuer,
        "authorize_url": f"{auth_url}/application/o/authorize/",
        "token_url": f"{auth_url}/application/o/token/",
        "userinfo_url": f"{auth_url}/application/o/userinfo/",
    }


async def _authentik(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    json: dict[str, Any] | list[Any] | None = None,
    data: dict[str, Any] | str | bytes | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    base_headers = {
        "Content-Type": "application/x-www-form-urlencoded",
    }
    async with httpx.AsyncClient() as client:
        return await client.request(
            method=method.upper(),
            url=url,
            headers={**base_headers, **(headers or {})},
            params=params,
            json=json,
            data=data,
            timeout=timeout,
        )


async def get_authentik_token(oauth_url: str, oauth_code: str) -> str:
    """Get an access token from Authentik using client credentials."""
    authentik = _get_authentik_config()
    response = await _authentik(
        url=authentik["token_url"],
        method="POST",
        data={
            "grant_type": "authorization_code",
            "code": oauth_code,
            "redirect_uri": oauth_url,
            "client_id": authentik["client_id"],
            "client_secret": authentik["client_secret"],
        },
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to exchange authorization code for tokens",
        )
    data = response.json()
    return data.get("access_token")


async def get_authentik_userinfo(access_token: str) -> dict[str, Any]:
    """Get user info from Authentik using an access token."""
    authentik = _get_authentik_config()
    response = await _authentik(
        url=authentik["userinfo_url"],
        method="GET",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to retrieve user info from Authentik",
        )
    return response.json()
