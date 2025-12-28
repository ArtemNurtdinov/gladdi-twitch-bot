import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Callable, Awaitable

from app.ai.gen.domain.llm_client import LLMClient
from app.ai.gen.domain.models import AIMessage, Role
from app.minigame.domain.minigame_service import MinigameService
from app.minigame.application.add_word.add_used_words_use_case_provider import AddUsedWordsUseCaseProvider
from app.chat.application.chat_use_case_provider import ChatUseCaseProvider
from app.ai.gen.domain.conversation_service_provider import ConversationServiceProvider
from app.economy.application.economy_service_provider import EconomyServiceProvider
from app.minigame.application.get_used_words.get_used_words_use_case_provider import GetUsedWordsUseCaseProvider
from app.stream.application.stream_service_provider import StreamServiceProvider
from core.db import SessionLocal, db_ro_session
from app.economy.domain.models import TransactionType

logger = logging.getLogger(__name__)


class MinigameOrchestrator:
    DEFAULT_SLEEP_SECONDS = 60

    def __init__(
        self,
        minigame_service: MinigameService,
        economy_service_provider: EconomyServiceProvider,
        chat_use_case_provider: ChatUseCaseProvider,
        stream_service_provider: StreamServiceProvider,
        get_used_words_use_case_provider: GetUsedWordsUseCaseProvider,
        add_used_words_use_case_provider: AddUsedWordsUseCaseProvider,
        conversation_service_provider: ConversationServiceProvider,
        llm_client: LLMClient,
        system_prompt: str,
        prefix: str,
        command_guess_letter: str,
        command_guess_word: str,
        command_guess: str,
        command_rps: str,
        bot_nick_provider: Callable[[], str | None],
        send_channel_message: Callable[[str, str], Awaitable[None]],
    ):
        self.minigame_service = minigame_service
        self._economy_service_provider = economy_service_provider
        self._chat_use_case_provider = chat_use_case_provider
        self._stream_service_provider = stream_service_provider
        self._get_used_words_use_case_provider = get_used_words_use_case_provider
        self._add_used_words_use_case_provider = add_used_words_use_case_provider
        self._conversation_service_provider = conversation_service_provider
        self._llm_client = llm_client
        self._system_prompt = system_prompt
        self._prefix = prefix
        self._command_guess_letter = command_guess_letter
        self._command_guess_word = command_guess_word
        self._command_guess = command_guess
        self._command_rps = command_rps
        self._bot_nick_provider = bot_nick_provider
        self._send_channel_message = send_channel_message

    def _bot_name_lower(self) -> str:
        return self._bot_nick_provider().lower()

    async def run_tick(self, channel_name: str) -> int:
        rps_game_complete_time = self.minigame_service.check_rps_game_complete_time(channel_name, datetime.utcnow())
        if rps_game_complete_time:
            await self._finish_rps(channel_name)
            return self.DEFAULT_SLEEP_SECONDS

        await self._finish_expired_games()

        with db_ro_session() as db:
            active_stream = self._stream_service_provider.get(db).get_active_stream(channel_name)

        if not active_stream:
            return self.DEFAULT_SLEEP_SECONDS

        if not self.minigame_service.should_start_new_game(channel_name):
            return self.DEFAULT_SLEEP_SECONDS

        choice = random.choice(["number", "word", "rps"])

        if choice == "word":
            await self._start_word_game(channel_name)
        elif choice == "number":
            await self._start_number_game(channel_name)
        else:
            await self._start_rps_game(channel_name)

        return self.DEFAULT_SLEEP_SECONDS

    async def _finish_rps(self, channel_name: str):
        game = self.minigame_service.get_active_rps_game(channel_name)
        bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game, channel_name)

        if winners:
            share = max(1, game.bank // len(winners))
            with SessionLocal.begin() as db:
                for winner in winners:
                    self._economy_service_provider.get(db).add_balance(
                        channel_name, winner, share, TransactionType.MINIGAME_WIN, f"Победа в КНБ ({winning_choice})"
                    )
            winners_display = ", ".join(f"@{winner}" for winner in winners)
            message = (
                f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. "
                f"Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
            )
        else:
            message = (
                f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. "
                f"Победителей нет. Банк {game.bank} монет сгорает."
            )

        with SessionLocal.begin() as db:
            self._chat_use_case_provider.get(db).save_chat_message(channel_name, self._bot_name_lower(), message, datetime.utcnow())

        await self._send_channel_message(channel_name, message)
        await asyncio.sleep(60)

    async def _finish_expired_games(self):
        expired_games = self.minigame_service.check_expired_games()
        for channel, timeout_message in expired_games.items():
            await self._send_channel_message(channel, timeout_message)
            with SessionLocal.begin() as db:
                self._chat_use_case_provider.get(db).save_chat_message(channel, self._bot_name_lower(), timeout_message, datetime.utcnow())

    async def _start_word_game(self, channel_name: str):
        with db_ro_session() as db:
            used_words = self._get_used_words_use_case_provider.get(db).get_used_words(channel_name, limit=50)
            last_messages = self._chat_use_case_provider.get(db).get_last_chat_messages(channel_name, limit=50)

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
        avoid_clause = "\n\nНе используй ранее загаданные слова: " + ", ".join(sorted(set(used_words))) if used_words else ""

        prompt = (
            "Проанализируй последние сообщения из чата и выбери одно подходящее русское существительное (ОДНО слово),"
            " связанное по смыслу с обсуждаемыми темами. Придумай короткую подсказку-описание к нему. Не повторяйся в загаданных словах."
            + avoid_clause
            + '\nОтвет верни строго в JSON без дополнительного текста: {"word": "слово", "hint": "краткая подсказка"}.'
              "\nТребования: слово только из букв, без пробелов и дефисов; подсказка до 100 символов."
              "\n\nВот сообщения чата (ник: текст):\n"
            + chat_text
        )

        system_prompt = self._system_prompt
        ai_messages = [AIMessage(Role.SYSTEM, system_prompt), AIMessage(Role.USER, prompt)]

        response = await self._llm_client.generate_ai_response(ai_messages)

        with SessionLocal.begin() as db:
            self._conversation_service_provider.get(db).save_conversation_to_db(channel_name, prompt, response)

        data = json.loads(response)
        word = str(data.get("word", "")).strip()
        hint = str(data.get("hint", "")).strip()
        final_word = word.strip().lower()

        game = self.minigame_service.start_word_guess_game(channel_name, final_word, hint)
        with SessionLocal.begin() as db:
            self._add_used_words_use_case_provider.get(db).add_used_words(channel_name, final_word)

        masked = game.get_masked_word()
        game_message = (
            f"НОВАЯ ИГРА 'поле чудес'! Слово из {len(game.target_word)} букв. Подсказка: {hint}. "
            f"Слово: {masked}. Приз: до {self.minigame_service.WORD_GAME_MAX_PRIZE} монет. "
            f"Угадывайте буквы: {self._prefix}{self._command_guess_letter} <буква> или слово: {self._prefix}{self._command_guess_word} <слово>. "
            f"Время на игру: {self.minigame_service.WORD_GAME_DURATION_MINUTES} минут"
        )
        logger.info(f"Запущена новая игра 'поле чудес' в канале {channel_name}")

        await self._send_channel_message(channel_name, game_message)

        with SessionLocal.begin() as db:
            self._chat_use_case_provider.get(db).save_chat_message(channel_name, self._bot_name_lower(), game_message, datetime.utcnow())

    async def _start_number_game(self, channel_name: str):
        game = self.minigame_service.start_guess_number_game(channel_name)
        game_message = (
            f"🎯 НОВАЯ МИНИ-ИГРА! Угадай число от {game.min_number} до {game.max_number}! "
            f"Первый, кто угадает, получит приз до {self.minigame_service.GUESS_GAME_PRIZE} монет! "
            f"Используй: {self._prefix}{self._command_guess} [число]. "
            f"Время на игру: {self.minigame_service.GUESS_GAME_DURATION_MINUTES} минут ⏰"
        )
        logger.info(f"Запущена новая игра 'угадай число' в канале {channel_name}")

        await self._send_channel_message(channel_name, game_message)
        with SessionLocal.begin() as db:
            self._chat_use_case_provider.get(db).save_chat_message(channel_name, self._bot_name_lower(), game_message, datetime.utcnow())

    async def _start_rps_game(self, channel_name: str):
        self.minigame_service.start_rps_game(channel_name)
        game_message = (
            f"✊✌️🖐 НОВАЯ ИГРА КНБ! Банк старт: {MinigameService.RPS_BASE_BANK} монет + {MinigameService.RPS_ENTRY_FEE_PER_USER}"
            f" за каждого участника. "
            f"Участвовать: {self._prefix}{self._command_rps} <камень/ножницы/бумага> — взнос {MinigameService.RPS_ENTRY_FEE_PER_USER} монет. "
            f"Время на голосование: {MinigameService.RPS_GAME_DURATION_MINUTES} минуты ⏰"
        )
        logger.info(f"Запущена новая игра КНБ в канале {channel_name}")

        await self._send_channel_message(channel_name, game_message)
        with SessionLocal.begin() as db:
            self._chat_use_case_provider.get(db).save_chat_message(channel_name, self._bot_name_lower(), game_message, datetime.utcnow())
