from contextlib import AbstractContextManager, contextmanager

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from core.config import config

Base = declarative_base()

engine = create_engine(config.database.url, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_rw():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_ro():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_ro_session() -> AbstractContextManager[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
