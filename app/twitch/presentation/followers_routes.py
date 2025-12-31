from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.twitch.bootstrap.followers import get_followers_repo
from app.twitch.domain.followers.repo import FollowersRepository
from app.twitch.presentation.followers_schemas import FollowerResponse, FollowersListResponse

router = APIRouter(prefix="/followers", tags=["Followers"])


@router.get("", response_model=FollowersListResponse, summary="Текущие подписчики (активные)")
async def get_active_followers(
    channel_name: str,
    repo: FollowersRepository = Depends(get_followers_repo),
):
    followers = repo.list_active(channel_name)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/new", response_model=FollowersListResponse, summary="Новые подписчики с даты")
async def get_new_followers(
    channel_name: str,
    since: datetime = Query(..., description="Дата/время, от которой считать новых (followed_at >=)"),
    until: Optional[datetime] = Query(None, description="Опционально: верхняя граница (followed_at <=)"),
    repo: FollowersRepository = Depends(get_followers_repo),
):
    followers = repo.list_new_since(channel_name, since, until)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/unfollowed", response_model=FollowersListResponse, summary="Отписавшиеся с даты")
async def get_unfollowed_followers(
    channel_name: str,
    since: datetime = Query(..., description="Дата/время, от которой считать отписавшихся (unfollowed_at >=)"),
    until: Optional[datetime] = Query(None, description="Опционально: верхняя граница (unfollowed_at <=)"),
    repo: FollowersRepository = Depends(get_followers_repo),
):
    followers = repo.list_unfollowed_since(channel_name, since, until)
    return FollowersListResponse(followers=[FollowerResponse.model_validate(f, from_attributes=True) for f in followers])


@router.get("/{channel_name}/{user_name}", response_model=FollowerResponse, summary="Детали подписчика")
async def get_follower_detail(
    channel_name: str,
    user_name: str,
    repo: FollowersRepository = Depends(get_followers_repo),
):
    follower = repo.get_by_user_name(channel_name, user_name)
    if not follower:
        raise HTTPException(status_code=404, detail="Подписчик не найден")
    return FollowerResponse.model_validate(follower, from_attributes=True)
