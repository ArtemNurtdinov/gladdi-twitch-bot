from fastapi import Depends
from sqlalchemy.orm import Session

from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from app.follow.domain.repo import FollowersRepository
from core.db import get_db_ro


def get_followers_repo(db: Session = Depends(get_db_ro)) -> FollowersRepository:
    return FollowersRepositoryImpl(db)


