import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Cookie, HTTPException, status
from pwdlib import PasswordHash

from db.models.user import User
from db.session import SessionDep
from db.user import _get_user_by_username

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
HASH = PasswordHash.recommended()


def _get_password_hash(password: str) -> str:
    """Hash a password using the recommended hasher."""
    return HASH.hash(password)


def _verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return HASH.verify(plain_password, hashed_password)


def _authenticate_user(
    session: SessionDep, username: str, password: str
) -> User | None:
    """Authenticate a user by username and password."""
    user = _get_user_by_username(session=session, username=username)

    if not user:
        return None

    if not _verify_password(password, user.password):
        return None
    return user


def _create_access_token(
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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def _get_current_user(
    session: SessionDep,
    access_token: Annotated[str | None, Cookie()] = None,
) -> User | None:
    """Get the current user from a JWT token."""
    unauthorized_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        if access_token is None:
            logger.warning("No access token provided")
            raise unauthorized_exception

        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")

        if username is None:
            logger.warning("Access token missing 'sub' claim")
            raise unauthorized_exception

        user = _get_user_by_username(session=session, username=username)

        if user is None:
            logger.warning(f"User not found for username: {username}")
            raise unauthorized_exception
        return user
    except jwt.InvalidTokenError:
        raise unauthorized_exception
