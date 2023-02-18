from sqlalchemy import create_engine, Engine

from config import MYSQL_URL, POSTGRES_URL, SQLITE_URL


def mysql_engine_factory() -> Engine:
    return create_engine(MYSQL_URL)


def postgres_engine_factory() -> Engine:
    return create_engine(POSTGRES_URL)


def sqlite_engine_factory() -> Engine:
    return create_engine(SQLITE_URL)
