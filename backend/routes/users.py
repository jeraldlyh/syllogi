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
from lib.providers import (
    get_provider,
    get_provider_enum,
    validate_recommendation_provider_username,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class CreateOrUpdateMusicServerUserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    provider: MusicServerProvider = Field(min_length=1)
    password: str = Field(default="", max_length=256)
    lastfm_username: str = Field(default="", max_length=128)
    listenbrainz_username: str = Field(default="", max_length=128)


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
    responses={
        200: {
            "description": "Users retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "data": [
                            {
                                "id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1",
                                "username": "jerald",
                            }
                        ],
                    }
                }
            },
        },
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
                    "example": {
                        "success": True,
                        "data": {"id": "2baf7b6b-87de-4289-bdd8-42f138f8c9e1"},
                    }
                }
            },
        },
        400: {
            "description": "Duplicate user or invalid Last.fm username",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Music server user already exists: <username> for provider <provider>",
                        },
                    }
                }
            },
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 403,
                            "name": "Forbidden",
                            "message": "Admin access required",
                        },
                    }
                }
            },
        },
        404: {
            "description": "Unable to verify credentials",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 404,
                            "name": "Not Found",
                            "message": "Unable to verify credentials for user: <username>",
                        },
                    }
                }
            },
        },
    },
)
async def _create_music_server_user(
    item: CreateOrUpdateMusicServerUserRequest, session: SessionDep
):
    existing = get_music_server_user_by_username(
        session=session, username=item.username, provider=item.provider
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Music server user already exists: {item.username} for provider {item.provider}",
        )

    if item.provider == get_provider_enum():
        is_valid_password = await get_provider().verify_user_credentials(
            username=item.username, password=item.password
        )

        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to verify credentials for user: {item.username}",
            )

    await validate_recommendation_provider_username(
        lastfm=item.lastfm_username, listenbrainz=item.listenbrainz_username
    )

    user = MusicServerUser(
        username=item.username,
        provider=item.provider,
        password=encrypt(item.password),
        lastfm_username=item.lastfm_username,
        listenbrainz_username=item.listenbrainz_username,
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
                    "example": {
                        "success": True,
                        "data": {"message": "Music server user updated successfully"},
                    }
                }
            },
        },
        400: {
            "description": "User not found or invalid Last.fm username",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 400,
                            "name": "Bad Request",
                            "message": "Unable to find music server user: <id>",
                        },
                    }
                }
            },
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 403,
                            "name": "Forbidden",
                            "message": "Admin access required",
                        },
                    }
                }
            },
        },
        404: {
            "description": "Unable to verify credentials",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 404,
                            "name": "Not Found",
                            "message": "Unable to verify credentials for user: <username>",
                        },
                    }
                }
            },
        },
    },
)
async def _update_music_server_user(
    id: str, item: CreateOrUpdateMusicServerUserRequest, session: SessionDep
):
    user = get_music_server_user_by_id(session=session, user_id=id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unable to find music server user: {id}",
        )

    if item.password and item.provider == get_provider_enum():
        is_valid_password = await get_provider().verify_user_credentials(
            username=item.username, password=item.password
        )

        if not is_valid_password:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Unable to verify credentials for user: {item.username}",
            )
        user.password = encrypt(item.password)

    await validate_recommendation_provider_username(
        lastfm=item.lastfm_username, listenbrainz=item.listenbrainz_username
    )

    user.username = item.username
    user.provider = MusicServerProvider(item.provider)
    user.lastfm_username = item.lastfm_username
    user.listenbrainz_username = item.listenbrainz_username

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
                    "example": {
                        "success": True,
                        "data": {"message": "Music server user deleted successfully"},
                    }
                }
            },
        },
        403: {
            "description": "Admin access required",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 403,
                            "name": "Forbidden",
                            "message": "Admin access required",
                        },
                    }
                }
            },
        },
        404: {
            "description": "User not found",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": 404,
                            "name": "Not Found",
                            "message": "Unable to find music server user: <id>",
                        },
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unable to find music server user: {id}",
        )

    delete_music_server_user(session=session, user=user)

    return {"message": "Music server user deleted successfully"}
