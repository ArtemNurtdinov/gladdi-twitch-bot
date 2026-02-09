from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.ai.gen.infrastructure.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.chat.infrastructure.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.commands.ask.infrastructure.ask_uow import SqlAlchemyAskUnitOfWorkFactory
from app.commands.balance.infrastructure.balance_uow import SqlAlchemyBalanceUnitOfWorkFactory
from app.commands.battle.infrastructure.battle_uow import SqlAlchemyBattleUnitOfWorkFactory
from app.commands.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.commands.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.commands.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.commands.follow.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.commands.guess.infrastructure.guess_uow import SqlAlchemyGuessUnitOfWorkFactory
from app.commands.help.infrastructure.help_uow import SqlAlchemyHelpUnitOfWorkFactory
from app.commands.roll.infrastructure.roll_uow import SqlAlchemyRollUnitOfWorkFactory
from app.commands.shop.infrastructure.shop_uow import SqlAlchemyShopUnitOfWorkFactory
from app.commands.stats.infrastructure.stats_uow import SqlAlchemyStatsUnitOfWorkFactory
from app.commands.top_bottom.infrastructure.top_bottom_uow import SqlAlchemyTopBottomUnitOfWorkFactory
from app.commands.transfer.infrastructure.transfer_uow import SqlAlchemyTransferUnitOfWorkFactory
from app.follow.infrastructure.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.joke.infrastructure.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.minigame.infrastructure.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.minigame.infrastructure.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.stream.infrastructure.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.viewer.infrastructure.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from bootstrap.providers_bundle import ProvidersBundle
from core.types import SessionFactory


@dataclass(frozen=True)
class UowFactories:
    build_ask_uow_factory: Callable[[], SqlAlchemyAskUnitOfWorkFactory]
    build_chat_message_uow_factory: Callable[[], SqlAlchemyChatMessageUnitOfWorkFactory]
    build_joke_uow_factory: Callable[[], SqlAlchemyJokeUnitOfWorkFactory]
    build_chat_response_uow_factory: Callable[[], SqlAlchemyChatResponseUnitOfWorkFactory]
    build_chat_summarizer_uow_factory: Callable[[], SqlAlchemyChatSummarizerUnitOfWorkFactory]
    build_balance_uow_factory: Callable[[], SqlAlchemyBalanceUnitOfWorkFactory]
    build_battle_uow_factory: Callable[[], SqlAlchemyBattleUnitOfWorkFactory]
    build_bonus_uow_factory: Callable[[], SqlAlchemyBonusUnitOfWorkFactory]
    build_equipment_uow_factory: Callable[[], SqlAlchemyEquipmentUnitOfWorkFactory]
    build_guess_uow_factory: Callable[[], SqlAlchemyGuessUnitOfWorkFactory]
    build_help_uow_factory: Callable[[], SqlAlchemyHelpUnitOfWorkFactory]
    build_roll_uow_factory: Callable[[], SqlAlchemyRollUnitOfWorkFactory]
    build_shop_uow_factory: Callable[[], SqlAlchemyShopUnitOfWorkFactory]
    build_stats_uow_factory: Callable[[], SqlAlchemyStatsUnitOfWorkFactory]
    build_top_bottom_uow_factory: Callable[[], SqlAlchemyTopBottomUnitOfWorkFactory]
    build_transfer_uow_factory: Callable[[], SqlAlchemyTransferUnitOfWorkFactory]
    build_minigame_uow_factory: Callable[[], SqlAlchemyMinigameUnitOfWorkFactory]
    build_rps_uow_factory: Callable[[], SqlAlchemyRpsUnitOfWorkFactory]
    build_follow_age_uow_factory: Callable[[], SqlAlchemyFollowAgeUnitOfWorkFactory]
    build_followers_sync_uow_factory: Callable[[], SqlAlchemyFollowersSyncUnitOfWorkFactory]
    build_restore_stream_context_uow_factory: Callable[[], SqlAlchemyRestoreStreamContextUnitOfWorkFactory]
    build_stream_status_uow_factory: Callable[[], SqlAlchemyStreamStatusUnitOfWorkFactory]
    build_viewer_time_uow_factory: Callable[[], SqlAlchemyViewerTimeUnitOfWorkFactory]


def create_uow_factories(
    *,
    session_factory_rw: SessionFactory,
    session_factory_ro: SessionFactory,
    providers: ProvidersBundle,
) -> UowFactories:
    ai_providers = providers.ai_providers
    chat_providers = providers.chat_providers
    stream_providers = providers.stream_providers
    economy_providers = providers.economy_providers
    equipment_providers = providers.equipment_providers
    minigame_providers = providers.minigame_providers
    battle_providers = providers.battle_providers
    betting_providers = providers.betting_providers
    follow_providers = providers.follow_providers
    viewer_providers = providers.viewer_providers
    def build_ask_uow_factory() -> SqlAlchemyAskUnitOfWorkFactory:
        return SqlAlchemyAskUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_repo_provider=chat_providers.chat_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_chat_message_uow_factory() -> SqlAlchemyChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_repo_provider=chat_providers.chat_repo_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            stream_repo_provider=stream_providers.stream_repo_provider,
            viewer_repo_provider=viewer_providers.viewer_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_joke_uow_factory() -> SqlAlchemyJokeUnitOfWorkFactory:
        return SqlAlchemyJokeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            conversation_service_provider=ai_providers.conversation_service_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_chat_response_uow_factory() -> SqlAlchemyChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_chat_summarizer_uow_factory() -> SqlAlchemyChatSummarizerUnitOfWorkFactory:
        return SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_service_provider=stream_providers.stream_service_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_balance_uow_factory() -> SqlAlchemyBalanceUnitOfWorkFactory:
        return SqlAlchemyBalanceUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_battle_uow_factory() -> SqlAlchemyBattleUnitOfWorkFactory:
        return SqlAlchemyBattleUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
        )

    def build_bonus_uow_factory() -> SqlAlchemyBonusUnitOfWorkFactory:
        return SqlAlchemyBonusUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_service_provider=stream_providers.stream_service_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_equipment_uow_factory() -> SqlAlchemyEquipmentUnitOfWorkFactory:
        return SqlAlchemyEquipmentUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_guess_uow_factory() -> SqlAlchemyGuessUnitOfWorkFactory:
        return SqlAlchemyGuessUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_help_uow_factory() -> SqlAlchemyHelpUnitOfWorkFactory:
        return SqlAlchemyHelpUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_roll_uow_factory() -> SqlAlchemyRollUnitOfWorkFactory:
        return SqlAlchemyRollUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_shop_uow_factory() -> SqlAlchemyShopUnitOfWorkFactory:
        return SqlAlchemyShopUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            add_equipment_use_case_provider=equipment_providers.add_equipment_use_case_provider,
            equipment_exists_use_case_provider=equipment_providers.equipment_exists_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_stats_uow_factory() -> SqlAlchemyStatsUnitOfWorkFactory:
        return SqlAlchemyStatsUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_top_bottom_uow_factory() -> SqlAlchemyTopBottomUnitOfWorkFactory:
        return SqlAlchemyTopBottomUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_transfer_uow_factory() -> SqlAlchemyTransferUnitOfWorkFactory:
        return SqlAlchemyTransferUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_minigame_uow_factory() -> SqlAlchemyMinigameUnitOfWorkFactory:
        return SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
            stream_service_provider=stream_providers.stream_service_provider,
            get_used_words_use_case_provider=minigame_providers.get_used_words_use_case_provider,
            add_used_words_use_case_provider=minigame_providers.add_used_words_use_case_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_rps_uow_factory() -> SqlAlchemyRpsUnitOfWorkFactory:
        return SqlAlchemyRpsUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_follow_age_uow_factory() -> SqlAlchemyFollowAgeUnitOfWorkFactory:
        return SqlAlchemyFollowAgeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            chat_repo_provider=chat_providers.chat_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_followers_sync_uow_factory() -> SqlAlchemyFollowersSyncUnitOfWorkFactory:
        return SqlAlchemyFollowersSyncUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            followers_repository_provider=follow_providers.followers_repository_provider,
        )

    def build_restore_stream_context_uow_factory() -> SqlAlchemyRestoreStreamContextUnitOfWorkFactory:
        return SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_service_provider=stream_providers.stream_service_provider,
        )

    def build_stream_status_uow_factory() -> SqlAlchemyStreamStatusUnitOfWorkFactory:
        return SqlAlchemyStreamStatusUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            stream_service_provider=stream_providers.stream_service_provider,
            start_stream_use_case_provider=stream_providers.start_stream_use_case_provider,
            viewer_service_provider=viewer_providers.viewer_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_viewer_time_uow_factory() -> SqlAlchemyViewerTimeUnitOfWorkFactory:
        return SqlAlchemyViewerTimeUnitOfWorkFactory(
            session_factory_rw=session_factory_rw,
            session_factory_ro=session_factory_ro,
            viewer_service_provider=viewer_providers.viewer_service_provider,
            stream_service_provider=stream_providers.stream_service_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
        )

    return UowFactories(
        build_ask_uow_factory=build_ask_uow_factory,
        build_chat_message_uow_factory=build_chat_message_uow_factory,
        build_joke_uow_factory=build_joke_uow_factory,
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
