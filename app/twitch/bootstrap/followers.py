from fastapi import Depends
from sqlalchemy.orm import Session

from app.twitch.data.followers.followers_repository import FollowersRepositoryImpl
from app.twitch.domain.followers.repo import FollowersRepository
from core.db import get_db_ro


def get_followers_repo(db: Session = Depends(get_db_ro)) -> FollowersRepository:
    return FollowersRepositoryImpl(db)


