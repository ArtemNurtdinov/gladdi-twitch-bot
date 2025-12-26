from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.twitch.application.background.stream_status.handle_stream_status_use_case import HandleStreamStatusUseCase
from app.twitch.application.interaction.chat.handle_chat_message_use_case import HandleChatMessageUseCase
from app.twitch.application.background.chat_summary.handle_chat_summarizer_use_case import (
    HandleChatSummarizerUseCase,
)
from app.twitch.application.background.minigame_tick.handle_minigame_tick_use_case import (
    HandleMinigameTickUseCase,
)
from app.twitch.application.background.post_joke.handle_post_joke_use_case import HandlePostJokeUseCase
from app.twitch.application.background.token_checker.handle_token_checker_use_case import (
    HandleTokenCheckerUseCase,
)
from app.twitch.application.background.viewer_time.handle_viewer_time_use_case import HandleViewerTimeUseCase
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.bootstrap.twitch_bot_settings import TwitchBotSettings
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.chat_summarizer_job import ChatSummarizerJob
from app.twitch.presentation.background.minigame_tick_job import MinigameTickJob
from app.twitch.presentation.background.post_joke_job import PostJokeJob
from app.twitch.presentation.background.stream_status_job import StreamStatusJob
from app.twitch.presentation.background.token_checker_job import TokenCheckerJob
from app.twitch.presentation.background.viewer_time_job import ViewerTimeJob
from app.twitch.presentation.chat_event_service import ChatEventHandler
from app.twitch.presentation.command_registry import CommandRegistry
from app.twitch.presentation.twitch_bot import Bot
from core.db import SessionLocal, db_ro_session


class BotFactory:
    def __init__(self, deps: BotDependencies, settings: TwitchBotSettings):
        self._deps = deps
        self._settings = settings

    def create(self) -> Bot:
        bot = Bot(self._deps, self._settings)

        bot.set_minigame_orchestrator(self._create_minigame(bot))
        bot.set_background_tasks(self._create_background_tasks(bot))
        bot.set_command_registry(self._create_command_registry(bot))
        bot.set_chat_event_handler(self._create_chat_event_handler(bot))
        bot.restore_stream_context()
        return bot

    def _create_minigame(self, bot: Bot) -> MinigameOrchestrator:
        return MinigameOrchestrator(
            minigame_service=self._deps.minigame_service,
            economy_service_factory=self._deps.economy_service,
            chat_use_case_factory=self._deps.chat_use_case,
            stream_service_factory=self._deps.stream_service,
            get_used_words_use_case_factory=self._deps.get_used_words_use_case,
            add_used_word_use_case_factory=self._deps.add_used_word_use_case,
            ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
            llm_client=self._deps.llm_client,
            system_prompt=bot.SYSTEM_PROMPT_FOR_GROUP,
            prefix=self._settings.prefix,
            command_guess_letter=self._settings.command_guess_letter,
            command_guess_word=self._settings.command_guess_word,
            command_guess=self._settings.command_guess,
            command_rps=self._settings.command_rps,
            bot_nick_provider=lambda: bot.nick,
            send_channel_message=bot.send_channel_message,
        )

    def _create_background_tasks(self, bot: Bot) -> BotBackgroundTasks:
        return BotBackgroundTasks(
            runner=self._deps.background_runner,
            jobs=[
                PostJokeJob(
                    channel_name=self._settings.channel_name,
                    handle_post_joke_use_case=HandlePostJokeUseCase(
                    joke_service=self._deps.joke_service,
                    user_cache=self._deps.user_cache,
                    twitch_api_service=self._deps.twitch_api_service,
                        generate_response_fn=bot.generate_response_in_chat,
                    ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
                    chat_use_case_factory=self._deps.chat_use_case,
                    ),
                    db_session_provider=SessionLocal.begin,
                    send_channel_message=bot.send_channel_message,
                    bot_nick_provider=lambda: bot.nick,
                ),
                TokenCheckerJob(
                    handle_token_checker_use_case=HandleTokenCheckerUseCase(
                        twitch_auth=self._deps.twitch_auth,
                        interval_seconds=1000,
                    ),
                ),
                StreamStatusJob(
                    channel_name=self._settings.channel_name,
                    handle_stream_status_use_case=HandleStreamStatusUseCase(
                        user_cache=self._deps.user_cache,
                        twitch_api_service=self._deps.twitch_api_service,
                        stream_service_factory=self._deps.stream_service,
                        start_new_stream_use_case_factory=self._deps.start_new_stream_use_case,
                        viewer_service_factory=self._deps.viewer_service,
                        battle_use_case_factory=self._deps.battle_use_case,
                        economy_service_factory=self._deps.economy_service,
                        chat_use_case_factory=self._deps.chat_use_case,
                        ai_conversation_use_case_factory=self._deps.ai_conversation_use_case,
                        minigame_service=self._deps.minigame_service,
                        telegram_bot=self._deps.telegram_bot,
                        telegram_group_id=self._settings.group_id,
                        generate_response_fn=bot.generate_response_in_chat,
                        state=bot.chat_summary_state,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    state=bot.chat_summary_state,
                    stream_status_interval_seconds=self._settings.check_stream_status_interval_seconds,
                ),
                ChatSummarizerJob(
                    channel_name=self._settings.channel_name,
                    twitch_api_service=self._deps.twitch_api_service,
                    handle_chat_summarizer_use_case=HandleChatSummarizerUseCase(
                    stream_service_factory=self._deps.stream_service,
                    chat_use_case_factory=self._deps.chat_use_case,
                        generate_response_fn=bot.generate_response_in_chat,
                    ),
                    db_readonly_session_provider=lambda: db_ro_session(),
                    state=bot.chat_summary_state,
                ),
                MinigameTickJob(
                    channel_name=self._settings.channel_name,
                    handle_minigame_tick_use_case=HandleMinigameTickUseCase(
                    minigame_orchestrator=bot.minigame_orchestrator,
                    ),
                ),
                ViewerTimeJob(
                    channel_name=self._settings.channel_name,
                    handle_viewer_time_use_case=HandleViewerTimeUseCase(
                        viewer_service_factory=self._deps.viewer_service,
                        stream_service_factory=self._deps.stream_service,
                        economy_service_factory=self._deps.economy_service,
                        user_cache=self._deps.user_cache,
                        twitch_api_service=self._deps.twitch_api_service,
                    ),
                    db_session_provider=SessionLocal.begin,
                    db_readonly_session_provider=lambda: db_ro_session(),
                    bot_nick_provider=lambda: bot.nick,
                    check_interval_seconds=self._settings.check_viewers_interval_seconds,
                ),
            ],
        )

    def _create_command_registry(self, bot: Bot) -> CommandRegistry:
        return CommandRegistry(
            deps=self._deps,
            settings=self._settings,
            prefix=self._settings.prefix,
            bot_nick_provider=lambda: bot.nick,
            post_message_fn=bot.post_message_in_twitch_chat,
            generate_response_fn=bot.generate_response_in_chat,
            timeout_fn=bot.timeout_user
        )

    def _create_chat_event_handler(self, bot: Bot) -> ChatEventHandler:
        handle_chat_message = HandleChatMessageUseCase(
            chat_use_case_factory=self._deps.chat_use_case,
            economy_service_factory=self._deps.economy_service,
            stream_service_factory=self._deps.stream_service,
            viewer_service_factory=self._deps.viewer_service,
            intent_use_case=self._deps.intent_use_case,
            prompt_service=self._deps.prompt_service,
            generate_response_fn=bot.generate_response_in_chat,
        )
        return ChatEventHandler(
            handle_chat_message_use_case=handle_chat_message,
            db_session_provider=SessionLocal.begin,
            send_channel_message=bot.send_channel_message,
        )
