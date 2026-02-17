from fastapi import Depends

from app.economy.bootstrap import get_economy_policy_ro
from app.economy.domain.economy_policy import EconomyPolicy
from app.follow.bootstrap import get_followers_repo_ro
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from app.user.application.usecase.get_user_detail_use_case import GetUserDetailUseCase
from app.user.infrastructure.economy_user_balance_adapter import EconomyUserBalanceAdapter
from app.user.infrastructure.follow_user_detail_info_adapter import FollowUserDetailInfoAdapter
from app.user.infrastructure.viewer_user_sessions_adapter import ViewerUserSessionsAdapter
from app.viewer.application.viewer_query_service import ViewerQueryService
from app.viewer.bootstrap import get_viewer_service_ro


def get_get_user_detail_use_case(
    followers_repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
    economy_policy: EconomyPolicy = Depends(get_economy_policy_ro),
    viewer_service: ViewerQueryService = Depends(get_viewer_service_ro),
) -> GetUserDetailUseCase:
    info_adapter = FollowUserDetailInfoAdapter(followers_repo)
    balance_adapter = EconomyUserBalanceAdapter(economy_policy)
    sessions_adapter = ViewerUserSessionsAdapter(viewer_service)
    return GetUserDetailUseCase(
        user_detail_info_port=info_adapter,
        balance_port=balance_adapter,
        sessions_port=sessions_adapter,
    )
