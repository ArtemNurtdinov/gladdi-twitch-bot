from contextlib import AbstractContextManager, contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from core.config import load_config

Base = declarative_base()


_database_url: str | None = None


def configure_db(database_url: str) -> None:
    global _database_url
    _database_url = database_url
    _get_engine.cache_clear()
    _get_session_local.cache_clear()


@lru_cache
def _get_engine():
    database_url = _database_url or load_config().database.url
    return create_engine(database_url, echo=False)


@lru_cache
def _get_session_local():
    return sessionmaker(autocommit=False, autoflush=True, bind=_get_engine())


def get_engine():
    return _get_engine()


def get_sessionmaker():
    return _get_session_local()


def get_db():
    db = _get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_rw():
    db = _get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_ro():
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_ro_session() -> AbstractContextManager[Session]:
    db = _get_session_local()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_rw_session() -> AbstractContextManager[Session]:
    db = _get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
