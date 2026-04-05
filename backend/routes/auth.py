from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from db.models.user import User
from db.user import _create_user
from db.session import SessionDep
from lib.auth import (
    _authenticate_user,
    get_current_user,
    _create_access_token,
    _get_password_hash,
)
from lib.cron import scheduler

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class RegisterUserRequest(BaseModel):
    username: str
    password: str


@router.get(
    path="/users/me",
    summary="Get current user",
    description="Retrieve information about the currently authenticated user.",
)
async def read_me(user: Annotated[User, Depends(get_current_user)]) -> User:
    return user


@router.post(
    path="/login",
    summary="Login",
    description="Authenticate a user and return an access token.",
)
async def login(
    session: SessionDep, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    user = _authenticate_user(
        session=session, username=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = _create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@router.post(
    path="/register", summary="Register", description="Create a new user account."
)
async def register(session: SessionDep, item: RegisterUserRequest):
    existing_user = _authenticate_user(
        session=session, username=item.username, password=item.password
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(username=item.username, password=_get_password_hash(item.password))

    _create_user(session=session, user=new_user)
    access_token = _create_access_token(data={"sub": new_user.username})

    return Token(access_token=access_token, token_type="bearer")
