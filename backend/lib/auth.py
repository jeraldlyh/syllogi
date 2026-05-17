import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, HTTPException, Header, status
from pwdlib import PasswordHash

from db.models.user import User
from db.session import SessionDep
from db.user import (
    count_users,
    create_user,
    get_user_by_oauth_id,
    get_user_by_username,
    update_user,
)
from lib.env import get_environment_variable

logger = logging.getLogger(__name__)

AUTH_SECRET_KEY = get_environment_variable("AUTH_SECRET_KEY", ignore_error=False)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
HASH = PasswordHash.recommended()


def _get_password_hash(password: str) -> str:
    """Hash a password using the recommended hasher."""
    return HASH.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return HASH.verify(plain_password, hashed_password)


def authenticate_user(session: SessionDep, username: str, password: str) -> User | None:
    """Authenticate a user by username and password."""
    user = get_user_by_username(session=session, username=username)

    if not user:
        return None

    if not user.password or not _verify_password(password, user.password):
        return None
    return user


def create_access_token(
    data: dict,
    expires_delta: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_user(
    session: SessionDep,
    access_token: Annotated[str | None, Cookie()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> User | None:
    """Get the current user from a JWT token."""
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if access_token is None and authorization is None:
            logger.warning("No access token provided")
            raise unauthorized_exception

        token = access_token

        if token is None and authorization is not None:
            scheme, _, credentials = authorization.partition(" ")
            if scheme.lower() == "bearer":
                token = credentials

        if token is None:
            logger.warning("No access token found in cookies or headers")
            raise unauthorized_exception

        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            logger.warning("Access token missing 'sub' claim")
            raise unauthorized_exception

        user = get_user_by_username(session=session, username=username)

        if user is None:
            logger.warning(f"User not found for username: {username}")
            raise unauthorized_exception
        return user
    except jwt.InvalidTokenError:
        raise unauthorized_exception


def get_or_create_oauth_user(session: SessionDep, oauth_id: str, username: str) -> User:
    """Get an existing OAuth user or create a new one."""

    user = get_user_by_username(session=session, username=username)

    if user:
        user.oauth_id = oauth_id
        update_user(session=session, user=user)
        return user

    user = get_user_by_oauth_id(session=session, oauth_id=oauth_id)

    if user:
        return user

    is_first_user = count_users(session=session) == 0
    new_user = User(
        username=username,
        password="",
        oauth_id=oauth_id,
        is_admin=is_first_user,
    )
    create_user(session=session, user=new_user)
    return new_user
