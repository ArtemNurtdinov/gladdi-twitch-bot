from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.battle.application.usecase.battle_use_case import BattleUseCase
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.domain.repo import ChatRepository
from app.economy.domain.economy_policy import EconomyPolicy
from app.equipment.application.get_user_equipment_use_case import GetUserEquipmentUseCase
from app.follow.application.uow.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.follow.domain.repo import FollowersRepository
from app.follow.infrastructure.uow.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.uow.rps_uow import RpsUnitOfWorkFactory
from app.minigame.application.use_case.add_used_word_use_case import AddUsedWordsUseCase
from app.minigame.application.use_case.get_used_words_use_case import GetUsedWordsUseCase
from app.minigame.infrastructure.uow.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.minigame.infrastructure.uow.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from app.platform.command.followage.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository
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
    build_minigame_uow_factory: Callable[[], MinigameUnitOfWorkFactory]
    build_rps_uow_factory: Callable[[], RpsUnitOfWorkFactory]
    build_follow_age_uow_factory: Callable[[], FollowAgeUnitOfWorkFactory]
    build_followers_sync_uow_factory: Callable[[], FollowersSyncUnitOfWorkFactory]
    build_restore_stream_context_uow_factory: Callable[[], RestoreStreamContextUnitOfWorkFactory]
    build_stream_status_uow_factory: Callable[[], StreamStatusUnitOfWorkFactory]
    build_viewer_time_uow_factory: Callable[[], ViewerTimeUnitOfWorkFactory]


def create_uow_factories(
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    chat_use_case: ChatUseCase,
    chat_repository_provider: Provider[ChatRepository],
    platform_repository: PlatformRepository,
    system_prompt_repository_provider: Provider[SystemPromptRepository],
    conversation_service_provider: Provider[ConversationService],
    stream_repository_provider: Provider[StreamRepository],
    follow_repository_provider: Provider[FollowersRepository],
    viewer_repository_provider: Provider[ViewerRepository],
    economy_policy_provider: Provider[EconomyPolicy],
    get_user_equipment_use_case: GetUserEquipmentUseCase,
    get_used_words_use_case: GetUsedWordsUseCase,
    add_used_word_use_case: AddUsedWordsUseCase,
    battle_use_case: BattleUseCase,
) -> UowFactories:
    def build_minigame_uow_factory() -> MinigameUnitOfWorkFactory:
        return SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
            stream_repository_provider=stream_repository_provider,
            get_used_words_use_case=get_used_words_use_case,
            add_used_words_use_case=add_used_word_use_case,
            conversation_service_provider=conversation_service_provider,
            get_user_equipment_use_case=get_user_equipment_use_case,
        )

    def build_rps_uow_factory() -> RpsUnitOfWorkFactory:
        return SqlAlchemyRpsUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def build_follow_age_uow_factory() -> FollowAgeUnitOfWorkFactory:
        return SqlAlchemyFollowAgeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_repo_provider=chat_repository_provider,
            conversation_service_provider=conversation_service_provider,
            system_prompt_repository_provider=system_prompt_repository_provider,
            platform_repository=platform_repository,
        )

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
        build_minigame_uow_factory=build_minigame_uow_factory,
        build_rps_uow_factory=build_rps_uow_factory,
        build_follow_age_uow_factory=build_follow_age_uow_factory,
        build_followers_sync_uow_factory=build_followers_sync_uow_factory,
        build_restore_stream_context_uow_factory=build_restore_stream_context_uow_factory,
        build_stream_status_uow_factory=build_stream_status_uow_factory,
        build_viewer_time_uow_factory=build_viewer_time_uow_factory,
    )
