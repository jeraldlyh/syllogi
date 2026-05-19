import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from db.session import SessionDep
from lib.auth import (
    create_access_token,
    get_or_create_oauth_user,
)
from lib.authentik import (
    _get_authentik_config,
    get_authentik_token,
    get_authentik_userinfo,
)
from lib.env import get_environment_variable

router = APIRouter()


# NOTE: Might consider shifting to Redis if required
_oauth_states: dict[str, str] = {}


@router.get(
    path="/authorize",
    summary="Initiate Authentik OAuth login",
    description="Redirect the browser to the Authentik authorization endpoint.",
)
def oauth_authorize():
    config = _get_authentik_config()

    redirect_uri = (
        f"{str(get_environment_variable('NEXT_PUBLIC_URL')).rstrip('/')}/oauth/callback"
    )

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = redirect_uri

    params = {
        "response_type": "code",
        "client_id": config["client_id"],
        "redirect_uri": redirect_uri,
        "scope": "openid profile email",
        "state": state,
    }

    url = f"{config['authorize_url']}?{urlencode(params)}"
    return RedirectResponse(url=url, status_code=302)


@router.get(
    path="/callback",
    summary="Handle Authentik OAuth callback",
    description=(
        "Exchange the authorization code for tokens, fetch user info from Authentik, "
        "create or retrieve the local user, issue a session cookie, and redirect to the app."
    ),
)
async def oauth_callback(
    _: Response,
    session: SessionDep,
    code: str,
    state: str,
):
    if state not in _oauth_states:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OAuth state parameter",
        )
    redirect_uri = _oauth_states.pop(state)

    access_token = await get_authentik_token(oauth_url=redirect_uri, oauth_code=code)

    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to obtain access token from Authentik",
        )

    userinfo = await get_authentik_userinfo(access_token=access_token)
    oauth_id = userinfo.get("sub")
    username = userinfo.get("preferred_username") or userinfo.get("name") or oauth_id

    if not oauth_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth provider did not return a subject identifier",
        )

    if not username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OAuth provider did not return a username",
        )

    user = get_or_create_oauth_user(
        session=session, oauth_id=oauth_id, username=username
    )
    access_token = create_access_token(data={"sub": user.username})

    redirect_response = RedirectResponse(
        url=str(get_environment_variable("NEXT_PUBLIC_URL")), status_code=302
    )
    redirect_response.set_cookie(
        key="access_token", value=access_token, httponly=True, samesite="lax"
    )
    return redirect_response
