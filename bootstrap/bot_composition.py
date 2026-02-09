from collections.abc import Callable
from dataclasses import dataclass

from app.ai.bootstrap import build_ai_providers
from app.ai.gen.application.chat_response_use_case import ChatResponseUseCase
from app.ai.gen.infrastructure.chat_response_uow import SqlAlchemyChatResponseUnitOfWorkFactory
from app.battle.bootstrap import build_battle_providers
from app.betting.bootstrap import build_betting_providers
from app.chat.application.chat_summarizer_job import ChatSummarizerJob
from app.chat.application.handle_chat_summarizer_use_case import HandleChatSummarizerUseCase
from app.chat.bootstrap import build_chat_providers
from app.chat.infrastructure.chat_summarizer_uow import SqlAlchemyChatSummarizerUnitOfWorkFactory
from app.commands.ask.application.handle_ask_use_case import HandleAskUseCase
from app.commands.ask.infrastructure.ask_uow import SqlAlchemyAskUnitOfWorkFactory
from app.commands.ask.presentation.ask_command_handler import AskCommandHandler
from app.commands.balance.application.handle_balance_use_case import HandleBalanceUseCase
from app.commands.balance.infrastructure.balance_uow import SqlAlchemyBalanceUnitOfWorkFactory
from app.commands.balance.presentation.balance_command_handler import BalanceCommandHandler
from app.commands.battle.application.handle_battle_use_case import HandleBattleUseCase
from app.commands.battle.infrastructure.battle_uow import SqlAlchemyBattleUnitOfWorkFactory
from app.commands.battle.presentation.battle_command_handler import BattleCommandHandler
from app.commands.bonus.application.handle_bonus_use_case import HandleBonusUseCase
from app.commands.bonus.infrastructure.bonus_uow import SqlAlchemyBonusUnitOfWorkFactory
from app.commands.bonus.presentation.bonus_command_handler import BonusCommandHandler
from app.commands.chat.application.handle_chat_message_use_case import HandleChatMessageUseCase
from app.commands.chat.infrastructure.chat_message_uow import SqlAlchemyChatMessageUnitOfWorkFactory
from app.commands.chat.presentation.chat_event_handler import DefaultChatEventsHandler
from app.commands.presentation.commands_registry import CommandRegistry
from app.commands.equipment.application.handle_equipment_use_case import HandleEquipmentUseCase
from app.commands.equipment.infrastructure.equipment_uow import SqlAlchemyEquipmentUnitOfWorkFactory
from app.commands.equipment.presentation.equipment_command_handler import EquipmentCommandHandler
from app.commands.follow.application.get_followage_use_case import GetFollowageUseCase
from app.commands.follow.application.handle_followage_use_case import HandleFollowAgeUseCase
from app.commands.follow.infrastructure.follow_age_uow import SqlAlchemyFollowAgeUnitOfWorkFactory
from app.commands.follow.infrastructure.followage_uow import SimpleFollowageUnitOfWorkFactory
from app.commands.follow.presentation.followage_command_handler import FollowageCommandHandler
from app.commands.guess.application.handle_guess_use_case import HandleGuessUseCase
from app.commands.guess.infrastructure.guess_uow import SqlAlchemyGuessUnitOfWorkFactory
from app.commands.guess.presentation.guess_command_handler import GuessCommandHandler
from app.commands.guess.presentation.rps_command_handler import RpsCommandHandler
from app.commands.help.application.handle_help_use_case import HandleHelpUseCase
from app.commands.help.infrastructure.help_uow import SqlAlchemyHelpUnitOfWorkFactory
from app.commands.help.presentation.help_command_handler import HelpCommandHandler
from app.commands.roll.application.handle_roll_use_case import HandleRollUseCase
from app.commands.roll.infrastructure.roll_uow import SqlAlchemyRollUnitOfWorkFactory
from app.commands.roll.presentation.roll_command_handler import RollCommandHandler
from app.commands.shop.application.handle_shop_use_case import HandleShopUseCase
from app.commands.shop.infrastructure.shop_uow import SqlAlchemyShopUnitOfWorkFactory
from app.commands.shop.presentation.shop_command_handler import ShopCommandHandler
from app.commands.stats.application.handle_stats_use_case import HandleStatsUseCase
from app.commands.stats.infrastructure.stats_uow import SqlAlchemyStatsUnitOfWorkFactory
from app.commands.stats.presentation.stats_command_handler import StatsCommandHandler
from app.commands.top_bottom.application.handle_top_bottom_use_case import HandleTopBottomUseCase
from app.commands.top_bottom.infrastructure.top_bottom_uow import SqlAlchemyTopBottomUnitOfWorkFactory
from app.commands.top_bottom.presentation.top_bottom_command_handler import TopBottomCommandHandler
from app.commands.transfer.application.handle_transfer_use_case import HandleTransferUseCase
from app.commands.transfer.infrastructure.transfer_uow import SqlAlchemyTransferUnitOfWorkFactory
from app.commands.transfer.presentation.transfer_command_handler import TransferCommandHandler
from app.economy.bootstrap import build_economy_providers
from app.equipment.bootstrap import build_equipment_providers
from app.follow.application.handle_followers_sync_use_case import HandleFollowersSyncUseCase
from app.follow.bootstrap import build_follow_providers
from app.follow.infrastructure.followers_sync_uow import SqlAlchemyFollowersSyncUnitOfWorkFactory
from app.follow.infrastructure.jobs.followers_sync_job import FollowersSyncJob
from app.joke.application.handle_post_joke_use_case import HandlePostJokeUseCase
from app.joke.application.post_joke_job import PostJokeJob
from app.joke.bootstrap import build_joke_providers
from app.joke.infrastructure.joke_uow import SqlAlchemyJokeUnitOfWorkFactory
from app.minigame.application.handle_minigame_tick_use_case import HandleMinigameTickUseCase
from app.minigame.application.handle_rps_use_case import HandleRpsUseCase
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.application.minigame_tick_job import MinigameTickJob
from app.minigame.bootstrap import build_minigame_providers
from app.minigame.infrastructure.minigame_uow import SqlAlchemyMinigameUnitOfWorkFactory
from app.minigame.infrastructure.rps_uow import SqlAlchemyRpsUnitOfWorkFactory
from app.moderation.application.moderation_service import ModerationService
from app.platform.application.handle_token_checker_use_case import HandleTokenCheckerUseCase
from app.platform.application.token_checker_job import TokenCheckerJob
from app.platform.auth import PlatformAuth
from app.platform.bot.bot import Bot
from app.platform.bot.bot_settings import BotSettings
from app.platform.providers import PlatformProviders
from app.stream.application.handle_restore_stream_context_use_case import HandleRestoreStreamContextUseCase
from app.stream.application.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.stream.application.model import RestoreStreamJobDTO
from app.stream.application.stream_status_job import StreamStatusJob
from app.stream.bootstrap import build_stream_providers
from app.stream.infrastructure.chat_response_adapter import ChatResponseAdapter
from app.stream.infrastructure.restore_stream_context_uow import SqlAlchemyRestoreStreamContextUnitOfWorkFactory
from app.stream.infrastructure.stream_status_uow import SqlAlchemyStreamStatusUnitOfWorkFactory
from app.stream.infrastructure.telegram_adapter import TelegramNotificationAdapter
from app.user.bootstrap import build_user_providers
from app.viewer.application.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.viewer.application.viewer_time_job import ViewerTimeJob
from app.viewer.bootstrap import build_viewer_providers
from app.viewer.infrastructure.viewer_time_uow import SqlAlchemyViewerTimeUnitOfWorkFactory
from bootstrap.telegram_provider import build_telegram_providers
from core.background.tasks import BackgroundTasks
from core.bootstrap.background import build_background_providers
from core.chat.interfaces import CommandRouter
from core.chat.outbound import ChatOutbound
from core.db import db_ro_session, db_rw_session


@dataclass
class BotComposition:
    bot: Bot
    chat_client: ChatOutbound
    platform_providers: PlatformProviders


async def build_bot_composition(
    *,
    access_token: str,
    refresh_token: str,
    tg_bot_token: str,
    llmbox_host: str,
    intent_detector_host: str,
    client_id: str,
    client_secret: str,
    settings: BotSettings,
    platform_auth_factory: Callable[[str, str, str, str], PlatformAuth],
    platform_providers_builder: Callable[[PlatformAuth], PlatformProviders],
    chat_client_factory: Callable[[PlatformAuth, BotSettings, str | None], ChatOutbound],
    command_router_builder: Callable[[BotSettings, CommandRegistry, Bot], CommandRouter],
) -> BotComposition:
    auth = platform_auth_factory(access_token, refresh_token, client_id, client_secret)
    platform_providers = platform_providers_builder(auth)
    streaming_platform = platform_providers.streaming_platform

    stream_providers = build_stream_providers(streaming_platform)
    ai_providers = build_ai_providers(llmbox_host=llmbox_host, intent_detector_host=intent_detector_host)
    chat_providers = build_chat_providers()
    follow_providers = build_follow_providers(streaming_platform)
    joke_providers = build_joke_providers()
    user_providers = build_user_providers(streaming_platform)
    viewer_providers = build_viewer_providers()
    economy_providers = build_economy_providers()
    equipment_providers = build_equipment_providers()
    minigame_providers = build_minigame_providers()
    battle_providers = build_battle_providers()
    betting_providers = build_betting_providers()
    background_providers = build_background_providers()
    telegram_providers = build_telegram_providers(tg_bot_token=tg_bot_token)

    bot_user = await streaming_platform.get_user_by_login(settings.bot_name)
    bot_user_id = bot_user.id if bot_user else None
    chat_client = chat_client_factory(platform_providers.platform_auth, settings, bot_user_id)

    def build_ask_uow_factory() -> SqlAlchemyAskUnitOfWorkFactory:
        return SqlAlchemyAskUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_repo_provider=chat_providers.chat_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_chat_message_uow_factory() -> SqlAlchemyChatMessageUnitOfWorkFactory:
        return SqlAlchemyChatMessageUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_repo_provider=chat_providers.chat_repo_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            stream_repo_provider=stream_providers.stream_repo_provider,
            viewer_repo_provider=viewer_providers.viewer_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_joke_uow_factory() -> SqlAlchemyJokeUnitOfWorkFactory:
        return SqlAlchemyJokeUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            conversation_service_provider=ai_providers.conversation_service_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_chat_response_uow_factory() -> SqlAlchemyChatResponseUnitOfWorkFactory:
        return SqlAlchemyChatResponseUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_chat_summarizer_uow_factory() -> SqlAlchemyChatSummarizerUnitOfWorkFactory:
        return SqlAlchemyChatSummarizerUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            stream_service_provider=stream_providers.stream_service_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_balance_uow_factory() -> SqlAlchemyBalanceUnitOfWorkFactory:
        return SqlAlchemyBalanceUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_battle_uow_factory() -> SqlAlchemyBattleUnitOfWorkFactory:
        return SqlAlchemyBattleUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
        )

    def build_bonus_uow_factory() -> SqlAlchemyBonusUnitOfWorkFactory:
        return SqlAlchemyBonusUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            stream_service_provider=stream_providers.stream_service_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_equipment_uow_factory() -> SqlAlchemyEquipmentUnitOfWorkFactory:
        return SqlAlchemyEquipmentUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_guess_uow_factory() -> SqlAlchemyGuessUnitOfWorkFactory:
        return SqlAlchemyGuessUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_help_uow_factory() -> SqlAlchemyHelpUnitOfWorkFactory:
        return SqlAlchemyHelpUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_roll_uow_factory() -> SqlAlchemyRollUnitOfWorkFactory:
        return SqlAlchemyRollUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            get_user_equipment_use_case_provider=equipment_providers.get_user_equipment_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_shop_uow_factory() -> SqlAlchemyShopUnitOfWorkFactory:
        return SqlAlchemyShopUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            add_equipment_use_case_provider=equipment_providers.add_equipment_use_case_provider,
            equipment_exists_use_case_provider=equipment_providers.equipment_exists_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_stats_uow_factory() -> SqlAlchemyStatsUnitOfWorkFactory:
        return SqlAlchemyStatsUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            betting_service_provider=betting_providers.betting_service_provider,
            battle_use_case_provider=battle_providers.battle_use_case_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_top_bottom_uow_factory() -> SqlAlchemyTopBottomUnitOfWorkFactory:
        return SqlAlchemyTopBottomUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_transfer_uow_factory() -> SqlAlchemyTransferUnitOfWorkFactory:
        return SqlAlchemyTransferUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_minigame_uow_factory() -> SqlAlchemyMinigameUnitOfWorkFactory:
        return SqlAlchemyMinigameUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
            stream_service_provider=stream_providers.stream_service_provider,
            get_used_words_use_case_provider=minigame_providers.get_used_words_use_case_provider,
            add_used_words_use_case_provider=minigame_providers.add_used_words_use_case_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_rps_uow_factory() -> SqlAlchemyRpsUnitOfWorkFactory:
        return SqlAlchemyRpsUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            economy_policy_provider=economy_providers.economy_policy_provider,
            chat_use_case_provider=chat_providers.chat_use_case_provider,
        )

    def build_follow_age_uow_factory() -> SqlAlchemyFollowAgeUnitOfWorkFactory:
        return SqlAlchemyFollowAgeUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            chat_repo_provider=chat_providers.chat_repo_provider,
            conversation_service_provider=ai_providers.conversation_service_provider,
        )

    def build_followers_sync_uow_factory() -> SqlAlchemyFollowersSyncUnitOfWorkFactory:
        return SqlAlchemyFollowersSyncUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            followers_repository_provider=follow_providers.followers_repository_provider,
        )

    def build_restore_stream_context_uow_factory() -> SqlAlchemyRestoreStreamContextUnitOfWorkFactory:
        return SqlAlchemyRestoreStreamContextUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            stream_service_provider=stream_providers.stream_service_provider,
        )

    def build_stream_status_uow_factory() -> SqlAlchemyStreamStatusUnitOfWorkFactory:
        return SqlAlchemyStreamStatusUnitOfWorkFactory(
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
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
            session_factory_rw=db_rw_session,
            session_factory_ro=db_ro_session,
            viewer_service_provider=viewer_providers.viewer_service_provider,
            stream_service_provider=stream_providers.stream_service_provider,
            economy_policy_provider=economy_providers.economy_policy_provider,
        )

    def build_chat_response_use_case(system_prompt: str) -> ChatResponseUseCase:
        return ChatResponseUseCase(
            unit_of_work_factory=build_chat_response_uow_factory(),
            llm_client=ai_providers.llm_client,
            system_prompt=system_prompt,
        )

    def build_minigame(bot: Bot, system_prompt: str, outbound: ChatOutbound) -> MinigameOrchestrator:
        return MinigameOrchestrator(
            minigame_service=minigame_providers.minigame_service,
            unit_of_work_factory=build_minigame_uow_factory(),
            llm_client=ai_providers.llm_client,
            system_prompt=system_prompt,
            prefix=settings.prefix,
            command_guess_letter=settings.command_guess_letter,
            command_guess_word=settings.command_guess_word,
            command_guess=settings.command_guess,
            command_rps=settings.command_rps,
            bot_nick=bot.nick,
            send_channel_message=outbound.send_channel_message,
        )

    def build_background_tasks(bot: Bot, chat_response_use_case: ChatResponseUseCase, outbound: ChatOutbound) -> BackgroundTasks:
        send_channel_message = outbound.send_channel_message
        notification_port = TelegramNotificationAdapter(telegram_providers.telegram_bot)
        chat_response_port = ChatResponseAdapter(chat_response_use_case)
        return BackgroundTasks(
            runner=background_providers.runner,
            jobs=[
                PostJokeJob(
                    channel_name=settings.channel_name,
                    handle_post_joke_use_case=HandlePostJokeUseCase(
                        joke_service=joke_providers.joke_service,
                        user_cache=user_providers.user_cache,
                        stream_info=stream_providers.stream_info_port,
                        chat_response_use_case=chat_response_use_case,
                        unit_of_work_factory=build_joke_uow_factory(),
                    ),
                    send_channel_message=send_channel_message,
                    bot_nick=bot.nick,
                ),
                TokenCheckerJob(
                    handle_token_checker_use_case=HandleTokenCheckerUseCase(
                        platform_auth=platform_providers.platform_auth, interval_seconds=1000
                    ),
                ),
                StreamStatusJob(
                    channel_name=settings.channel_name,
                    handle_stream_status_use_case=HandleStreamStatusUseCase(
                        user_cache=user_providers.user_cache,
                        stream_status_port=stream_providers.stream_status_port,
                        unit_of_work_factory=build_stream_status_uow_factory(),
                        minigame_service=minigame_providers.minigame_service,
                        notification_port=notification_port,
                        notification_group_id=settings.group_id,
                        chat_response_port=chat_response_port,
                        state=bot.chat_summary_state,
                    ),
                    stream_status_interval_seconds=settings.check_stream_status_interval_seconds,
                ),
                ChatSummarizerJob(
                    channel_name=settings.channel_name,
                    handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                        unit_of_work_factory=build_chat_summarizer_uow_factory(),
                        chat_response_use_case=chat_response_use_case,
                    ),
                    chat_summary_state=bot.chat_summary_state,
                ),
                MinigameTickJob(
                    channel_name=settings.channel_name,
                    handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                        minigame_orchestrator=bot.minigame_orchestrator,
                    ),
                ),
                ViewerTimeJob(
                    channel_name=settings.channel_name,
                    handle_viewer_time_use_case=HandleViewerTimeUseCase(
                        unit_of_work_factory=build_viewer_time_uow_factory(),
                        user_cache=user_providers.user_cache,
                        stream_chatters_port=stream_providers.stream_chatters_port,
                    ),
                    bot_nick=bot.nick,
                    check_interval_seconds=settings.check_viewers_interval_seconds,
                ),
                FollowersSyncJob(
                    channel_name=settings.channel_name,
                    handle_followers_sync_use_case=HandleFollowersSyncUseCase(
                        followers_port=follow_providers.followers_port,
                        unit_of_work_factory=build_followers_sync_uow_factory(),
                    ),
                    interval_seconds=settings.sync_followers_interval_seconds,
                ),
            ],
        )

    def build_command_registry(
        bot_nick: str, chat_response_use_case: ChatResponseUseCase, system_prompt: str, outbound: ChatOutbound
    ) -> CommandRegistry:
        prefix = settings.prefix
        post_message_fn = outbound.post_message
        moderation_service = ModerationService(moderation_port=platform_providers.streaming_platform, user_cache=user_providers.user_cache)
        ask_uow_factory = build_ask_uow_factory()

        followage_command_handler = FollowageCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_followage,
            handle_follow_age_use_case=HandleFollowAgeUseCase(
                chat_repo_provider=chat_providers.chat_repo_provider,
                conversation_repo_provider=ai_providers.conversation_repo_provider,
                get_followage_use_case=GetFollowageUseCase(
                    unit_of_work_factory=SimpleFollowageUnitOfWorkFactory(follow_providers.followage_port),
                ),
                chat_response_use_case=chat_response_use_case,
                unit_of_work_factory=build_follow_age_uow_factory(),
                system_prompt=system_prompt,
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        ask_command_handler = AskCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_gladdi,
            handle_ask_use_case=HandleAskUseCase(
                get_intent_from_text_use_case=ai_providers.get_intent_use_case,
                prompt_service=ai_providers.prompt_service,
                unit_of_work_factory=ask_uow_factory,
                system_prompt=system_prompt,
                chat_response_use_case=chat_response_use_case,
            ),
            post_message_fn=post_message_fn,
            bot_nick=bot_nick,
        )
        battle_command_handler = BattleCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_fight,
            handle_battle_use_case=HandleBattleUseCase(
                unit_of_work_factory=build_battle_uow_factory(),
                chat_response_use_case=chat_response_use_case,
                calculate_timeout_use_case_provider=equipment_providers.calculate_timeout_use_case_provider,
            ),
            chat_moderation=moderation_service,
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        roll_command_handler = RollCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_roll,
            handle_roll_use_case=HandleRollUseCase(
                unit_of_work_factory=build_roll_uow_factory(),
                roll_cooldown_use_case_provider=equipment_providers.roll_cooldown_use_case_provider,
                calculate_timeout_use_case_provider=equipment_providers.calculate_timeout_use_case_provider,
            ),
            chat_moderation=moderation_service,
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        balance_command_handler = BalanceCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_balance,
            handle_balance_use_case=HandleBalanceUseCase(
                unit_of_work_factory=build_balance_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        bonus_command_handler = BonusCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_bonus,
            handle_bonus_use_case=HandleBonusUseCase(
                unit_of_work_factory=build_bonus_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        transfer_command_handler = TransferCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_transfer,
            handle_transfer_use_case=HandleTransferUseCase(
                unit_of_work_factory=build_transfer_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        shop_command_handler = ShopCommandHandler(
            command_prefix=prefix,
            command_shop_name=settings.command_shop,
            command_buy_name=settings.command_buy,
            handle_shop_use_case=HandleShopUseCase(
                unit_of_work_factory=build_shop_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        equipment_command_handler = EquipmentCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_equipment,
            command_shop=settings.command_shop,
            handle_equipment_use_case=HandleEquipmentUseCase(
                unit_of_work_factory=build_equipment_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        top_bottom_command_handler = TopBottomCommandHandler(
            command_prefix=prefix,
            command_top=settings.command_top,
            command_bottom=settings.command_bottom,
            handle_top_bottom_use_case=HandleTopBottomUseCase(
                unit_of_work_factory=build_top_bottom_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        stats_command_handler = StatsCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_stats,
            handle_stats_use_case=HandleStatsUseCase(
                unit_of_work_factory=build_stats_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        commands = {
            settings.command_balance,
            settings.command_bonus,
            f"{settings.command_roll} [сумма]",
            f"{settings.command_transfer} @ник сумма",
            settings.command_shop,
            f"{settings.command_buy} название",
            settings.command_equipment,
            settings.command_top,
            settings.command_bottom,
            settings.command_stats,
            settings.command_fight,
            f"{settings.command_gladdi} текст",
            settings.command_followage,
        }
        help_command_handler = HelpCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_help,
            handle_help_use_case=HandleHelpUseCase(unit_of_work_factory=build_help_uow_factory()),
            commands=commands,
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        guess_command_handler = GuessCommandHandler(
            command_prefix=prefix,
            command_guess=settings.command_guess,
            command_guess_letter=settings.command_guess_letter,
            command_guess_word=settings.command_guess_word,
            handle_guess_use_case=HandleGuessUseCase(
                minigame_service=minigame_providers.minigame_service,
                unit_of_work_factory=build_guess_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )
        rps_command_handler = RpsCommandHandler(
            command_prefix=prefix,
            command_name=settings.command_rps,
            handle_rps_use_case=HandleRpsUseCase(
                minigame_service=minigame_providers.minigame_service,
                unit_of_work_factory=build_rps_uow_factory(),
            ),
            bot_nick=bot_nick,
            post_message_fn=post_message_fn,
        )

        return CommandRegistry(
            followage_command_handler=followage_command_handler,
            ask_command_handler=ask_command_handler,
            battle_command_handler=battle_command_handler,
            roll_command_handler=roll_command_handler,
            balance_command_handler=balance_command_handler,
            bonus_command_handler=bonus_command_handler,
            transfer_command_handler=transfer_command_handler,
            shop_command_handler=shop_command_handler,
            equipment_command_handler=equipment_command_handler,
            top_bottom_command_handler=top_bottom_command_handler,
            stats_command_handler=stats_command_handler,
            help_command_handler=help_command_handler,
            guess_command_handler=guess_command_handler,
            rps_command_handler=rps_command_handler,
        )

    def build_chat_event_handler(
        chat_response_use_case: ChatResponseUseCase, system_prompt: str, outbound: ChatOutbound
    ) -> DefaultChatEventsHandler:
        handle_chat_message = HandleChatMessageUseCase(
            unit_of_work_factory=build_chat_message_uow_factory(),
            get_intent_from_text_use_case=ai_providers.get_intent_use_case,
            prompt_service=ai_providers.prompt_service,
            system_prompt=system_prompt,
            chat_response_use_case=chat_response_use_case,
        )
        return DefaultChatEventsHandler(
            handle_chat_message_use_case=handle_chat_message,
            send_channel_message=outbound.send_channel_message,
        )

    def restore_stream_context() -> None:
        if not settings.channel_name:
            return
        restore_stream_job_dto = RestoreStreamJobDTO(settings.channel_name)
        HandleRestoreStreamContextUseCase(
            unit_of_work_factory=build_restore_stream_context_uow_factory(),
            minigame_service=minigame_providers.minigame_service,
        ).handle(restore_stream_job_dto)

    bot = Bot(platform_providers, user_providers, settings)
    system_prompt = ai_providers.prompt_service.get_system_prompt_for_group()
    chat_response_use_case = build_chat_response_use_case(system_prompt)

    bot.set_minigame_orchestrator(build_minigame(bot, system_prompt, chat_client))
    bot.set_background_tasks(build_background_tasks(bot, chat_response_use_case, chat_client))
    command_registry = build_command_registry(bot.nick, chat_response_use_case, system_prompt, chat_client)
    chat_client.set_chat_event_handler(build_chat_event_handler(chat_response_use_case, system_prompt, chat_client))
    chat_client.set_router(command_router_builder(settings, command_registry, bot))
    restore_stream_context()

    return BotComposition(bot=bot, chat_client=chat_client, platform_providers=platform_providers)
