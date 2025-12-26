import logging
from collections import Counter
from datetime import datetime
from typing import Callable, ContextManager, Protocol

import telegram
from sqlalchemy.orm import Session

from app.battle.application.battle_use_case import BattleUseCase
from app.economy.domain.economy_service import EconomyService
from app.economy.domain.models import TransactionType
from app.minigame.domain.minigame_service import MinigameService
from app.stream.application.start_new_stream_use_case import StartNewStreamUseCase
from app.stream.domain.models import StreamStatistics
from app.viewer.domain.viewer_session_service import ViewerTimeService
from app.twitch.application.background.stream_status.dto import StreamStatusDTO
from app.twitch.application.shared import ChatResponder, StreamServiceProvider
from app.twitch.infrastructure.cache.user_cache_service import UserCacheService
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.chat.application.chat_use_case import ChatUseCase
from app.ai.application.conversation_service import ConversationService

logger = logging.getLogger(__name__)


class ChatSummaryStateProtocol(Protocol):
    current_stream_summaries: list[str]
    last_chat_summary_time: datetime | None


class HandleStreamStatusUseCase:

    def __init__(
        self,
        user_cache: UserCacheService,
        twitch_api_service: TwitchApiService,
        stream_service_provider: StreamServiceProvider,
        start_new_stream_use_case_factory: Callable[[Session], StartNewStreamUseCase],
        viewer_service_factory: Callable[[Session], ViewerTimeService],
        battle_use_case_factory: Callable[[Session], BattleUseCase],
        economy_service_factory: Callable[[Session], EconomyService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        minigame_service: MinigameService,
        telegram_bot: telegram.Bot,
        telegram_group_id: int,
        chat_responder: ChatResponder,
        state: ChatSummaryStateProtocol,
    ):
        self._user_cache = user_cache
        self._twitch_api_service = twitch_api_service
        self._stream_service_provider = stream_service_provider
        self._start_new_stream_use_case_factory = start_new_stream_use_case_factory
        self._viewer_service_factory = viewer_service_factory
        self._battle_use_case_factory = battle_use_case_factory
        self._economy_service_factory = economy_service_factory
        self._chat_use_case_factory = chat_use_case_factory
        self._ai_conversation_use_case_factory = ai_conversation_use_case_factory
        self._minigame_service = minigame_service
        self._telegram_bot = telegram_bot
        self._telegram_group_id = telegram_group_id
        self._chat_responder = chat_responder
        self._state = state

    async def handle(
        self,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
        dto: StreamStatusDTO,
    ) -> None:
        broadcaster_id = await self._user_cache.get_user_id(dto.channel_name)

        if not broadcaster_id:
            logger.error(f"Не удалось получить ID канала {dto.channel_name}. Пропускаем проверку.")
            return

        stream_status = await self._twitch_api_service.get_stream_status(broadcaster_id)
        if stream_status is None:
            logger.error(f"Не удалось получить статус стрима для канала {dto.channel_name}")
            return

        game_name = stream_status.stream_data.game_name if stream_status.is_online and stream_status.stream_data else None
        title = stream_status.stream_data.title if stream_status.is_online and stream_status.stream_data else None

        logger.info(f"Статус стрима: {stream_status}")

        with db_readonly_session_provider() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(dto.channel_name)

        if stream_status.is_online and active_stream is None:
            logger.info(f"Стрим начался: {game_name} - {title}")
            await self._handle_stream_start(dto.channel_name, game_name, title, db_session_provider)

        elif not stream_status.is_online and active_stream is not None:
            await self._handle_stream_end(dto.channel_name, active_stream, db_session_provider, db_readonly_session_provider)

        elif stream_status.is_online and active_stream:
            if active_stream.game_name != game_name or active_stream.title != title:
                with db_session_provider() as db:
                    self._stream_service_provider.get(db).update_stream_metadata(active_stream.id, game_name, title)
                logger.info(f"Обновлены метаданные стрима: игра='{game_name}', название='{title}'")

    async def _handle_stream_start(
        self,
        channel_name: str,
        game_name: str | None,
        title: str | None,
        db_session_provider: Callable[[], ContextManager[Session]],
    ):
        started_at = datetime.utcnow()
        try:
            with db_session_provider() as db:
                start_stream_use_case = self._start_new_stream_use_case_factory(db)
                start_stream_use_case(channel_name, started_at, game_name, title)
            self._minigame_service.set_stream_start_time(channel_name, started_at)
            await self._stream_announcement(channel_name, game_name, title)
            self._state.current_stream_summaries = []
        except Exception as e:
            logger.error(f"Ошибка при создании стрима: {e}")

    async def _handle_stream_end(
        self,
        channel_name: str,
        active_stream,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
    ):
        finish_time = datetime.utcnow()
        logger.info("Стрим завершён")
        with db_session_provider() as db:
            self._stream_service_provider.get(db).end_stream(active_stream.id, finish_time)
            self._viewer_service_factory(db).finish_stream_sessions(active_stream.id, finish_time)
            total_viewers = self._viewer_service_factory(db).get_unique_viewers_count(active_stream.id)
            self._stream_service_provider.get(db).update_stream_total_viewers(active_stream.id, total_viewers)
            logger.info(f"Стрим завершен в БД: ID {active_stream.id}")

        self._minigame_service.reset_stream_state(channel_name)

        with db_readonly_session_provider() as db:
            battles = self._battle_use_case_factory(db).get_battles(channel_name, active_stream.started_at)

        with db_readonly_session_provider() as db:
            chat_messages = self._chat_use_case_factory(db).get_chat_messages(
                channel_name=channel_name,
                from_time=active_stream.started_at,
                to_time=finish_time,
            )

        stats = self._build_stream_statistics(chat_messages, battles)

        try:
            await self._stream_summarize(stats, channel_name, active_stream.started_at, finish_time, db_session_provider, db_readonly_session_provider)
        except Exception as e:
            logger.error(f"Ошибка при вызове stream_summarize: {e}")

    @staticmethod
    def _build_stream_statistics(chat_messages, battles) -> StreamStatistics:
        total_messages = len(chat_messages)
        unique_users = len(set(msg.user_name for msg in chat_messages))
        user_counts = Counter(msg.user_name for msg in chat_messages)
        top_user = user_counts.most_common(1)[0][0] if user_counts else None

        total_battles = len(battles)
        winner_counts = Counter(b.winner for b in battles)
        top_winner = winner_counts.most_common(1)[0][0] if battles else None

        return StreamStatistics(total_messages, unique_users, top_user, total_battles, top_winner)

    async def _stream_announcement(self,  channel_name: str, game_name: str | None, title: str | None):
        prompt = (
            f"Начался стрим. Категория: {game_name}, название: {title}. "
            f"Сгенерируй краткий анонс для телеграм канала. Ссылка на трансляцию: https://twitch.tv/{channel_name}"
        )
        result = self._chat_responder.generate_response(prompt, channel_name)
        try:
            await self._telegram_bot.send_message(chat_id=self._telegram_group_id, text=result)
        except Exception as e:
            logger.error(f"Ошибка отправки анонса в Telegram: {e}")

    async def _stream_summarize(
        self,
        stream_stat: StreamStatistics,
        channel_name: str,
        stream_start_dt,
        stream_end_dt,
        db_session_provider: Callable[[], ContextManager[Session]],
        db_readonly_session_provider: Callable[[], ContextManager[Session]],
    ):
        logger.info("Создание итогового отчёта о стриме")

        if self._state.last_chat_summary_time is None:
            self._state.last_chat_summary_time = stream_start_dt

        with db_readonly_session_provider() as db:
            last_messages = self._chat_use_case_factory(db).get_chat_messages(
                channel_name=channel_name,
                from_time=self._state.last_chat_summary_time,
                to_time=stream_end_dt,
            )
            if last_messages:
                chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
                prompt = (
                    f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                    f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
                )
                result = self._chat_responder.generate_response(prompt, channel_name)
                self._state.current_stream_summaries.append(result)

        duration = stream_end_dt - stream_start_dt
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        top_user = stream_stat.top_user if stream_stat.top_user else "нет"

        stream_stat_message = f"Длительность: {duration_str}. Сообщений: {stream_stat.total_messages}. Самый активный пользователь: {top_user}."

        if stream_stat.total_battles > 0:
            stream_stat_message += f" Битв за стрим: {stream_stat.total_battles}. Главный победитель: {stream_stat.top_winner}"

        if stream_stat.top_user and stream_stat.top_user != "нет":
            reward_amount = 200
            with db_session_provider() as db:
                user_balance = self._economy_service_factory(db).add_balance(
                    channel_name,
                    stream_stat.top_user,
                    reward_amount,
                    TransactionType.SPECIAL_EVENT,
                    "Награда за самую высокую активность в стриме",
                )
                stream_stat_message += (
                    f"{stream_stat.top_user} получает награду {reward_amount} монет за активность! Баланс: {user_balance.balance} монет."
                )

        logger.info(f"Статистика стрима: {stream_stat_message}")

        prompt = f"Трансляция была завершена. Статистика:\n{stream_stat_message}"

        if self._state.current_stream_summaries:
            summary_text = "\n".join(self._state.current_stream_summaries)
            prompt += f"\n\nВыжимки из того, что происходило в чате: {summary_text}"

        prompt += f"\n\nНа основе предоставленной информации подведи краткий итог трансляции"
        result = self._chat_responder.generate_response(prompt, channel_name)

        with db_session_provider() as db:
            self._ai_conversation_use_case_factory(db).save_conversation_to_db(channel_name, prompt, result)

        self._state.current_stream_summaries = []
        self._state.last_chat_summary_time = None

        await self._telegram_bot.send_message(chat_id=self._telegram_group_id, text=result)

