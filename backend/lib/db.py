import os
from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine


def get_connection_string() -> str:
    username = os.getenv("DATABASE_USERNAME")
    password = os.getenv("DATABASE_PASSWORD")
    url = os.getenv("DATABASE_URL")
    name = os.getenv("DATABASE_NAME")

    if username and password and url and name:
        return f"postgresql://{username}:{password}@{url}/{name}"
    return "postgresql://syllogi:syllogi@localhost:5432/syllogi"


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]

engine = create_engine(get_connection_string())


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
