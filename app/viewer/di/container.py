from sqlalchemy.orm import Session

from app.economy.domain.economy_policy import EconomyPolicy
from app.follow.domain.repo import FollowersRepository
from app.platform.domain.repository import PlatformRepository
from app.viewer.application.port.viewer_cache_port import ViewerCachePort
from app.viewer.application.usecase.get_viewer_detail_use_case import GetViewerDetailUseCase
from app.viewer.infrastructure.adapter.economy_viewer_balance_adapter import EconomyViewerBalanceAdapter
from app.viewer.infrastructure.adapter.follow_viewer_detail_info_adapter import FollowViewerDetailInfoAdapter
from app.viewer.infrastructure.adapter.viewer_viewer_sessions_adapter import ViewerViewerSessionsAdapter
from app.viewer.infrastructure.cache.viewer_cache_service import ViewerCacheService
from app.viewer.session.application.usecase.get_user_sessions_use_case import GetUserSessionsUseCase
from app.viewer.session.domain.repository import ViewerRepository
from app.viewer.session.infrastructure.session_repository import ViewerRepositoryImpl
from core.provider import Provider


class ViewerContainer:
    def __init__(self):
        self.viewer_repository_provider: Provider[ViewerRepository] = Provider(self.viewer_repository)

    def viewer_repository(self, session: Session) -> ViewerRepository:
        return ViewerRepositoryImpl(session)

    def get_user_sessions_use_case(self, session: Session) -> GetUserSessionsUseCase:
        viewer_repository = self.viewer_repository(session)
        return GetUserSessionsUseCase(viewer_repository)

    def get_viewer_detail_use_case(
        self, followers_repo: FollowersRepository, economy_policy: EconomyPolicy, session: Session
    ) -> GetViewerDetailUseCase:
        user_info_adapter = FollowViewerDetailInfoAdapter(followers_repo)
        balance_adapter = EconomyViewerBalanceAdapter(economy_policy)
        get_user_session_use_case = self.get_user_sessions_use_case(session)
        sessions_adapter = ViewerViewerSessionsAdapter(get_user_session_use_case)
        return GetViewerDetailUseCase(user_info_adapter, balance_adapter, sessions_adapter)

    def viewer_cache(self, platform_repository: PlatformRepository) -> ViewerCachePort:
        return ViewerCacheService(platform_repository)
