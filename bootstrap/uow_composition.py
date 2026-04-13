from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.ai.gen.application.uow.chat_response_uow import ChatResponseUnitOfWorkFactory
from app.ai.gen.conversation.domain.conversation_service import ConversationService
from app.ai.gen.infrastructure.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.chat.application.uow.chat_summarizer_uow import ChatSummarizerUnitOfWorkFactory
from app.chat.application.usecase.chat_use_case import ChatUseCase
from app.chat.domain.repo import ChatRepository
from app.chat.infrastructure.uow.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.follow.application.uow.followers_sync_uow import FollowersSyncUnitOfWorkFactory
from app.follow.infrastructure.uow.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.application.uow.rps_uow import RpsUnitOfWorkFactory
from app.minigame.infrastructure.uow.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.minigame.infrastructure.uow.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.platform.chat.application.chat_message_uow import ChatMessageUnitOfWorkFactory
from app.platform.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.platform.command.balance.application.balance_uow import BalanceUnitOfWorkFactory
from app.platform.command.balance.infrastructure.balance_uow import SqlAlchemyBalanceUnitOfWorkFactory
from app.platform.command.battle.application.battle_uow import BattleUnitOfWorkFactory
from app.platform.command.battle.infrastructure.battle_uow import SqlAlchemyBattleUnitOfWorkFactory
from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.platform.command.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.platform.command.equipment.application.equipment_uow import EquipmentUnitOfWorkFactory
from app.platform.command.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from app.platform.command.followage.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.platform.command.guess.application.guess_uow import GuessUnitOfWorkFactory
from app.platform.command.guess.infrastructure.guess_uow import SqlAlchemyGuessUnitOfWorkFactory
from app.platform.command.help.application.help_uow import HelpUnitOfWorkFactory
from app.platform.command.help.infrastructure.help_uow import SqlAlchemyHelpUnitOfWorkFactory
from app.platform.command.roll.application.roll_uow import RollUnitOfWorkFactory
from app.platform.command.roll.infrastructure.roll_uow import SqlAlchemyRollUnitOfWorkFactory
from app.platform.command.shop.application.shop_uow import ShopUnitOfWorkFactory
from app.platform.command.shop.infrastructure.shop_uow import SqlAlchemyShopUnitOfWorkFactory
from app.platform.command.stats.application.stats_uow import StatsUnitOfWorkFactory
from app.platform.command.stats.infrastructure.stats_uow import SqlAlchemyStatsUnitOfWorkFactory
from app.platform.command.top_bottom.application.top_bottom_uow import TopBottomUnitOfWorkFactory
from app.platform.command.top_bottom.infrastructure.top_bottom_uow import SqlAlchemyTopBottomUnitOfWorkFactory
from app.platform.command.transfer.application.transfer_uow import TransferUnitOfWorkFactory
from app.platform.command.transfer.infrastructure.transfer_uow import SqlAlchemyTransferUnitOfWorkFactory
from app.platform.domain.repository import PlatformRepository
from app.stream.application.uow.restore_stream_context_uow import RestoreStreamContextUnitOfWorkFactory
from app.stream.application.uow.stream_status_uow import StreamStatusUnitOfWorkFactory
from app.stream.domain.repo import StreamRepository
from app.stream.infrastructure.uow.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.uow.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.viewer.session.application.uow.viewer_time_uow import ViewerTimeUnitOfWorkFactory
from app.viewer.session.infrastructure.uow.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from bootstrap.providers_bundle import ProvidersBundle
from core.provider import Provider
from core.types import SessionFactory


@dataclass(frozen=True)
class UowFactories:
    build_chat_message_uow_factory: Callable[[], ChatMessageUnitOfWorkFactory]
    build_chat_response_uow_factory: Callable[[], ChatResponseUnitOfWorkFactory]
    build_chat_summarizer_uow_factory: Callable[[], ChatSummarizerUnitOfWorkFactory]
    build_balance_uow_factory: Callable[[], BalanceUnitOfWorkFactory]
    build_battle_uow_factory: Callable[[], BattleUnitOfWorkFactory]
    build_bonus_uow_factory: Callable[[], BonusUnitOfWorkFactory]
    build_equipment_uow_factory: Callable[[], EquipmentUnitOfWorkFactory]
    build_guess_uow_factory: Callable[[], GuessUnitOfWorkFactory]
    build_help_uow_factory: Callable[[], HelpUnitOfWorkFactory]
    build_roll_uow_factory: Callable[[], RollUnitOfWorkFactory]
    build_shop_uow_factory: Callable[[], ShopUnitOfWorkFactory]
    build_stats_uow_factory: Callable[[], StatsUnitOfWorkFactory]
    build_top_bottom_uow_factory: Callable[[], TopBottomUnitOfWorkFactory]
    build_transfer_uow_factory: Callable[[], TransferUnitOfWorkFactory]
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
    providers: ProvidersBundle,
    chat_use_case: ChatUseCase,
    chat_repository_provider: Provider[ChatRepository],
    platform_repository: PlatformRepository,
    system_prompt_repository_provider: Provider[SystemPromptRepository],
    conversation_service_provider: Provider[ConversationService],
    stream_repository_provider: Provider[StreamRepository],
) -> UowFactories:
    economy_providers = providers.economy_providers
    equipment_providers = providers.equipment_providers
    minigame_providers = providers.minigame_providers
    battle_providers = providers.battle_providers
    betting_providers = providers.betting_providers
    follow_providers = providers.follow_providers
    viewer_providers = providers.viewer_providers

    def build_chat_message_uow_factory() -> ChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_repo_provider=chat_repository_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            stream_repo_provider=stream_repository_provider,
            viewer_repo_provider=viewer_providers.viewer_repo_provider,
            conversation_service_provider=conversation_service_provider,
            system_prompt_repository_provider=system_prompt_repository_provider,
        )

    def build_chat_response_uow_factory() -> ChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            conversation_service_provider=conversation_service_provider,
        )

    def build_chat_summarizer_uow_factory() -> ChatSummarizerUnitOfWorkFactory:
        return SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_repository_provider=stream_repository_provider,
            chat_use_case=chat_use_case,
        )

    def build_balance_uow_factory() -> BalanceUnitOfWorkFactory:
        return SqlAlchemyBalanceUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def build_battle_uow_factory() -> BattleUnitOfWorkFactory:
        return SqlAlchemyBattleUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
            conversation_service_provider=conversation_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
        )

    def build_bonus_uow_factory() -> BonusUnitOfWorkFactory:
        return SqlAlchemyBonusUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_repository_provider=stream_repository_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def build_equipment_uow_factory() -> EquipmentUnitOfWorkFactory:
        return SqlAlchemyEquipmentUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case=chat_use_case,
        )

    def build_guess_uow_factory() -> GuessUnitOfWorkFactory:
        return SqlAlchemyGuessUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
            get_user_equipment_use_case=equipment_providers.get_user_equipment_use_case_provider,
        )

    def build_help_uow_factory() -> HelpUnitOfWorkFactory:
        return SqlAlchemyHelpUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_use_case=chat_use_case,
        )

    def build_roll_uow_factory() -> RollUnitOfWorkFactory:
        return SqlAlchemyRollUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case=chat_use_case,
        )

    def build_shop_uow_factory() -> ShopUnitOfWorkFactory:
        return SqlAlchemyShopUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            add_equipment_use_case_provider=equipment_providers.add_equipment_use_case_provider,
            equipment_exists_use_case_provider=equipment_providers.equipment_exists_use_case_provider,
            chat_use_case=chat_use_case,
            shop_item_repository_provider=equipment_providers.shop_item_repository_provider,
        )

    def build_stats_uow_factory() -> StatsUnitOfWorkFactory:
        return SqlAlchemyStatsUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            chat_use_case=chat_use_case,
        )

    def build_top_bottom_uow_factory() -> TopBottomUnitOfWorkFactory:
        return SqlAlchemyTopBottomUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def build_transfer_uow_factory() -> TransferUnitOfWorkFactory:
        return SqlAlchemyTransferUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
        )

    def build_minigame_uow_factory() -> MinigameUnitOfWorkFactory:
        return SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
            stream_repository_provider=stream_repository_provider,
            get_used_words_use_case_provider=minigame_providers.get_used_words_use_case_provider,
            add_used_words_use_case_provider=minigame_providers.add_used_words_use_case_provider,
            conversation_service_provider=conversation_service_provider,
            get_user_equipment_use_case=equipment_providers.get_user_equipment_use_case_provider,
        )

    def build_rps_uow_factory() -> RpsUnitOfWorkFactory:
        return SqlAlchemyRpsUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
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
            followers_repository_provider=follow_providers.followers_repository_provider,
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
            viewer_repository_provider=viewer_providers.viewer_repo_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case=chat_use_case,
            conversation_service_provider=conversation_service_provider,
        )

    def build_viewer_time_uow_factory() -> ViewerTimeUnitOfWorkFactory:
        return SqlAlchemyViewerTimeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            viewer_repository_provider=viewer_providers.viewer_repo_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            stream_repository_provider=stream_repository_provider,
        )

    return UowFactories(
        build_chat_message_uow_factory=build_chat_message_uow_factory,
        build_chat_response_uow_factory=build_chat_response_uow_factory,
        build_chat_summarizer_uow_factory=build_chat_summarizer_uow_factory,
        build_balance_uow_factory=build_balance_uow_factory,
        build_battle_uow_factory=build_battle_uow_factory,
        build_bonus_uow_factory=build_bonus_uow_factory,
        build_equipment_uow_factory=build_equipment_uow_factory,
        build_guess_uow_factory=build_guess_uow_factory,
        build_help_uow_factory=build_help_uow_factory,
        build_roll_uow_factory=build_roll_uow_factory,
        build_shop_uow_factory=build_shop_uow_factory,
        build_stats_uow_factory=build_stats_uow_factory,
        build_top_bottom_uow_factory=build_top_bottom_uow_factory,
        build_transfer_uow_factory=build_transfer_uow_factory,
        build_minigame_uow_factory=build_minigame_uow_factory,
        build_rps_uow_factory=build_rps_uow_factory,
        build_follow_age_uow_factory=build_follow_age_uow_factory,
        build_followers_sync_uow_factory=build_followers_sync_uow_factory,
        build_restore_stream_context_uow_factory=build_restore_stream_context_uow_factory,
        build_stream_status_uow_factory=build_stream_status_uow_factory,
        build_viewer_time_uow_factory=build_viewer_time_uow_factory,
    )
