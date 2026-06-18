import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from db.models.music_server_user import MusicServerProvider, MusicServerUser
from db.music_server_user import (
    create_music_server_user,
    delete_music_server_user,
    get_music_server_user_by_id,
    get_music_server_user_by_username,
    get_music_server_users,
    update_music_server_user,
)
from db.session import SessionDep
from lib.auth import require_admin
from lib.crypto import encrypt
from lib.providers import get_provider

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateOrUpdateMusicServerUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    provider: MusicServerProvider
    password: str = Field(default="", max_length=256)


@router.get(
    path="",
    summary="Get music server users",
    description="Retrieve a list of all users from the configured music server.",
    responses={
        200: {
            "description": "Users retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {"id": "a8f1b0c2", "name": "jerald"},
                            {"id": "9f8e7d6c", "name": "guest"},
                        ],
                    }
                }
            },
        }
    },
)
async def _get_users():
    provider = get_provider()
    users = await provider.get_users()

    return [user.to_dict() for user in users]


@router.get(
    path="/provider",
    summary="Get saved music server users",
    description="Retrieve a list of all saved music server users.",
    dependencies=[Depends(require_admin)],
    responses={
        200: {
            "description": "Users retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                            "username": "jerald",
                        }
                    ],
                }
            },
        }
    },
)
def _get_music_server_users(session: SessionDep):
    users = get_music_server_users(session=session)
    return [user.to_dict(exclude={"password"}) for user in users]


@router.post(
    path="/provider",
    summary="Create music server user",
    description="Create a new music server user.",
    dependencies=[Depends(require_admin)],
    responses={
        200: {
            "description": "User created successfully",
            "content": {
                "application/json": {
                    "example": {"id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1"},
                }
            },
        }
    },
)
def _create_music_server_user(
    item: CreateOrUpdateMusicServerUserRequest, session: SessionDep
):
    provider = MusicServerProvider(item.provider)

    existing = get_music_server_user_by_username(
        session=session, username=item.username, provider=provider
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Music server user already exists: {item.username} for provider {item.provider}",
        )

    user = MusicServerUser(
        username=item.username,
        provider=provider,
        password=encrypt(item.password),
    )
    create_music_server_user(session=session, user=user)
    return {"id": str(user.id)}


@router.put(
    path="/provider/{id}",
    summary="Update music server user",
    description="Update an existing music server user by its ID.",
    dependencies=[Depends(require_admin)],
    responses={
        200: {
            "description": "User updated successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Music server user updated successfully"},
                }
            },
        },
        400: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to find music server user: <user_id>",
                    }
                }
            },
        },
    },
)
def _update_music_server_user(
    id: str, item: CreateOrUpdateMusicServerUserRequest, session: SessionDep
):
    user = get_music_server_user_by_id(session=session, user_id=id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find music server user: {id}",
        )

    user.username = item.username
    user.provider = MusicServerProvider(item.provider)
    user.password = encrypt(item.password)

    update_music_server_user(session=session, user=user)

    return {"message": "Music server user updated successfully"}


@router.delete(
    path="/provider/{id}",
    summary="Delete music server user",
    description="Delete a music server user by its ID.",
    dependencies=[Depends(require_admin)],
    responses={
        200: {
            "description": "User deleted successfully",
            "content": {
                "application/json": {
                    "example": {"message": "Music server user deleted successfully"},
                }
            },
        },
        400: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Unable to find music server user: <user_id>",
                    }
                }
            },
        },
    },
)
def _delete_music_server_user(id: str, session: SessionDep):
    user = get_music_server_user_by_id(session=session, user_id=id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find music server user: {id}",
        )

    delete_music_server_user(session=session, user=user)

    return {"message": "Music server user deleted successfully"}
