from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.follow.di.container import FollowContainer
from app.presentation.deps import get_app


def get_follow_container(app: AppContainer = Depends(get_app)) -> FollowContainer:
    return app.follow
