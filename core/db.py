from contextlib import AbstractContextManager, contextmanager
from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from bootstrap.config_provider import get_config

Base = declarative_base()


@lru_cache
def _get_engine():
    cfg = get_config()
    return create_engine(cfg.database.url, echo=False)


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
    """Контекстный менеджер для RW-сессии с коммитом/ролбеком."""
    db = _get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
