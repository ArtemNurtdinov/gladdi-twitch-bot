from fastapi import Depends

from app.economy.bootstrap import get_economy_policy_ro
from app.economy.domain.economy_policy import EconomyPolicy
from app.follow.bootstrap import get_followers_repo_ro
from app.follow.infrastructure.followers_repository import FollowersRepositoryImpl
from app.viewer.application.usecase.get_viewer_detail_use_case import GetViewerDetailUseCase
from app.viewer.bootstrap import get_viewer_service_ro
from app.viewer.infrastructure.adapter.economy_viewer_balance_adapter import EconomyViewerBalanceAdapter
from app.viewer.infrastructure.adapter.follow_viewer_detail_info_adapter import FollowViewerDetailInfoAdapter
from app.viewer.infrastructure.adapter.viewer_viewer_sessions_adapter import ViewerViewerSessionsAdapter
from app.viewer.session.application.usecase.get_user_sessions_use_case import GetUserSessionsUseCase


def get_get_viewer_detail_use_case(
    followers_repo: FollowersRepositoryImpl = Depends(get_followers_repo_ro),
    economy_policy: EconomyPolicy = Depends(get_economy_policy_ro),
    viewer_service: GetUserSessionsUseCase = Depends(get_viewer_service_ro),
) -> GetViewerDetailUseCase:
    info_adapter = FollowViewerDetailInfoAdapter(followers_repo)
    balance_adapter = EconomyViewerBalanceAdapter(economy_policy)
    sessions_adapter = ViewerViewerSessionsAdapter(viewer_service)
    return GetViewerDetailUseCase(
        user_detail_info_port=info_adapter,
        balance_port=balance_adapter,
        sessions_port=sessions_adapter,
    )
