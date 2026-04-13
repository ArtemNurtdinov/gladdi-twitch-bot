from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.economy.domain.economy_policy import EconomyPolicy
from app.follow.application.uow.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.uow.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.stream.application.uow.restore_stream_context_uow import RestoreStreamContextUnitOfWorkFactory
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.uow.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.uow.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.viewer.session.application.uow.viewer_time_uow import ViewerTimeUnitOfWorkFactory
from app.viewer.session.domain.repository import ViewerRepository
from app.viewer.session.infrastructure.uow.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from core.provider import Provider
from core.types import SessionFactory


@dataclass(frozen=True)
class UowFactories:
    build_followers_sync_uow_factory: Callable[[], FollowersSyncUnitOfWorkFactory]
    build_restore_stream_context_uow_factory: Callable[[], RestoreStreamContextUnitOfWorkFactory]
    build_stream_status_uow_factory: Callable[[], StreamStatusUnitOfWorkFactory]
    build_viewer_time_uow_factory: Callable[[], ViewerTimeUnitOfWorkFactory]


def create_uow_factories(
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    chat_use_case: ChatUseCase,
    conversation_service_provider: Provider[ConversationService],
    stream_repository_provider: Provider[StreamRepository],
    follow_repository_provider: Provider[FollowersRepository],
    viewer_repository_provider: Provider[ViewerRepository],
    economy_policy_provider: Provider[EconomyPolicy],
    battle_use_case: BattleUseCase,
) -> UowFactories:
    def build_followers_sync_uow_factory() -> FollowersSyncUnitOfWorkFactory:
        return SqlAlchemyFollowersSyncUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            followers_repository_provider=follow_repository_provider,
        )

    def build_restore_stream_context_uow_factory() -> RestoreStreamContextUnitOfWorkFactory:
        return SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_repository_provider=stream_repository_provider,
        )

    def build_stream_status_uow_factory() -> StreamStatusUnitOfWorkFactory:
        return SqlAlchemyStreamStatusUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_repository_provider=stream_repository_provider,
            viewer_repository_provider=viewer_repository_provider,
            battle_use_case=battle_use_case,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
            conversation_service_provider=conversation_service_provider,
        )

    def build_viewer_time_uow_factory() -> ViewerTimeUnitOfWorkFactory:
        return SqlAlchemyViewerTimeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            viewer_repository_provider=viewer_repository_provider,
            economy_policy_provider=economy_policy_provider,
            stream_repository_provider=stream_repository_provider,
        )

    return UowFactories(
        build_followers_sync_uow_factory=build_followers_sync_uow_factory,
        build_restore_stream_context_uow_factory=build_restore_stream_context_uow_factory,
        build_stream_status_uow_factory=build_stream_status_uow_factory,
        build_viewer_time_uow_factory=build_viewer_time_uow_factory,
    )
