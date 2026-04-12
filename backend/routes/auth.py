from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from db.models.user import User
from db.session import SessionDep
from db.user import _create_user
from lib.auth import (
    _authenticate_user,
    _create_access_token,
    _get_current_user,
    _get_password_hash,
)

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str


class RegisterUserRequest(BaseModel):
    username: str
    password: str


@router.get(
    path="/me",
    summary="Get current user",
    description="Retrieve information about the currently authenticated user.",
    responses={
        200: {
            "description": "Current user retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {"id": "1", "username": "jerald"},
                    }
                }
            },
        }
    },
)
async def read_me(user: Annotated[User, Depends(_get_current_user)]) -> User:
    del user.password
    return user


@router.post(
    path="/login",
    summary="Login",
    description="Authenticate a user and return an access token.",
    responses={
        200: {
            "description": "Login successful",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "access_token": "<jwt_token>",
                            "token_type": "bearer",
                        },
                    }
                }
            },
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 401,
                            "name": "Unauthorized",
                            "message": "Incorrect username or password",
                        },
                    }
                }
            },
        },
    },
)
async def login(
    response: Response,
    session: SessionDep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
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
    response.set_cookie(
        key="access_token", value=access_token, httponly=True, samesite="lax"
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    path="/register",
    summary="Register",
    description="Create a new user account.",
    responses={
        200: {
            "description": "User registered successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": {
                            "access_token": "<jwt_token>",
                            "token_type": "bearer",
                        },
                    }
                }
            },
        },
        400: {
            "description": "Username already exists",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Username already exists",
                        },
                    }
                }
            },
        },
    },
)
async def register(response: Response, session: SessionDep, item: RegisterUserRequest):
    existing_user = _authenticate_user(
        session=session, username=item.username, password=item.password
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    new_user = User(
        username=item.username,
        password=_get_password_hash(item.password),
        oauth_id=None,
    )

    _create_user(session=session, user=new_user)
    access_token = _create_access_token(data={"sub": new_user.username})
    response.set_cookie(key="access_token", value=access_token, httponly=True)

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    path="/logout",
    summary="Logout",
    description="Logout the current user by clearing the access token cookie.",
    responses={
        200: {
            "description": "Logout successful",
            "content": {
                "application/json": {
                    "example": {"success": True, "data": "Logged out successfully"}
                }
            },
        }
    },
)
def logout(request: Request, response: Response):
    if request.cookies.get("access_token") is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    response.delete_cookie(key="access_token")
    return "Logged out successfully"
