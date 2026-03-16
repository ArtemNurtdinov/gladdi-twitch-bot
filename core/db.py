from contextlib import AbstractContextManager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config.domain.model.db import DatabaseConfig

Base = declarative_base()

_engine = None
_SessionLocal = None


def init_db(config: DatabaseConfig):
    global _engine, _SessionLocal
    _engine = create_engine(config.url, echo=False)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=_engine)


def get_session_local():
    if _SessionLocal is None:
        raise RuntimeError("Database not initialized. Call init_db first")
    return _SessionLocal


def get_db():
    db = get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_rw():
    db = get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_ro():
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_ro_session() -> AbstractContextManager[Session]:
    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_rw_session() -> AbstractContextManager[Session]:
    db = get_session_local()()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
