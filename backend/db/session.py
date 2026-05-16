from typing import Annotated

from fastapi import Depends
from sqlmodel import Session, SQLModel, create_engine

from lib.env import get_environment_variable


def get_connection_string() -> str:
    username = get_environment_variable("DATABASE_USERNAME")
    password = get_environment_variable("DATABASE_PASSWORD")
    url = get_environment_variable("DATABASE_URL")
    name = get_environment_variable("DATABASE_NAME")

    if username and password and url and name:
        return f"postgresql+psycopg://{username}:{password}@{url}/{name}"
    return "postgresql+psycopg://syllogi:syllogi@localhost:5432/syllogi"


def get_session():
    with Session(engine) as session:
        yield session


def get_isolated_session():
    return Session(engine)


SessionDep = Annotated[Session, Depends(get_session)]

engine = create_engine(get_connection_string())


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
