import asyncio
import json
import random
from collections.abc import Awaitable, Callable
from datetime import datetime

from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.economy.domain.models import TransactionType
from app.minigame.application.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_service import MinigameService
from core.provider import Provider
from core.types import SessionFactory


class MinigameOrchestrator:
    DEFAULT_SLEEP_SECONDS = 60

    def __init__(
        self,
        minigame_service: MinigameService,
        unit_of_work_factory: MinigameUnitOfWorkFactory,
        llm_repository: LLMRepository,
        system_prompt_repository_provider: Provider[SystemPromptRepository],
        db_ro_session: SessionFactory,
        prefix: str,
        command_guess_letter: str,
        command_guess_word: str,
        command_guess: str,
        command_rps: str,
        bot_nick: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
    ):
        self.minigame_service = minigame_service
        self._unit_of_work_factory = unit_of_work_factory
        self._llm_repository = llm_repository
        self._system_prompt_repository_provider = system_prompt_repository_provider
        self._db_ro_session = db_ro_session
        self._prefix = prefix
        self._command_guess_letter = command_guess_letter
        self._command_guess_word = command_guess_word
        self._command_guess = command_guess
        self._command_rps = command_rps
        self._bot_nick = bot_nick
        self._send_channel_message = send_channel_message

    def _bot_name_lower(self) -> str:
        return self._bot_nick.lower()

    async def run_tick(self, channel_name: str) -> int:
        rps_game_complete_time = self.minigame_service.check_rps_game_complete_time(channel_name, datetime.utcnow())
        if rps_game_complete_time:
            await self._finish_rps(channel_name)
            return self.DEFAULT_SLEEP_SECONDS

        await self._finish_expired_games()

        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(channel_name)

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
            with self._unit_of_work_factory.create() as uow:
                for winner in winners:
                    uow.economy_policy.add_balance(
                        channel_name=channel_name,
                        user_name=winner,
                        amount=share,
                        transaction_type=TransactionType.MINIGAME_WIN,
                        description=f"Победа в КНБ ({winning_choice})",
                    )
            winners_display = ", ".join(f"@{winner}" for winner in winners)
            message = (
                f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. "
                f"Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
            )
        else:
            message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name_lower(), content=message, current_time=datetime.utcnow()
            )

        await self._send_channel_message(channel_name, message)
        await asyncio.sleep(60)

    async def _finish_expired_games(self):
        expired_games = self.minigame_service.check_expired_games()
        for channel, timeout_message in expired_games.items():
            await self._send_channel_message(channel, timeout_message)
            with self._unit_of_work_factory.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=channel, user_name=self._bot_name_lower(), content=timeout_message, current_time=datetime.utcnow()
                )

    async def _start_word_game(self, channel_name: str):
        with self._unit_of_work_factory.create(read_only=True) as uow:
            used_words = uow.get_used_words_use_case.get_used_words(channel_name, limit=50)
            last_messages = uow.chat_use_case.get_last_chat_messages(channel_name, limit=50)

        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
        avoid_clause = "\n\nНе используй ранее загаданные слова: " + ", ".join(sorted(set(used_words))) if used_words else ""

        prompt = (
            "Проанализируй последние сообщения из чата и выбери (или придумай) существительное (ОДНО слово),"
            " связанное по смыслу с обсуждаемыми темами. Придумай короткую подсказку-описание к нему."
            + avoid_clause
            + '\nОтвет верни строго в JSON без дополнительного текста: {"word": "слово", "hint": "краткая подсказка"}.'
            "\nТребования: слово только из букв, без пробелов и дефисов; подсказка до 100 символов."
            "\n\nВот сообщения чата (ник: текст):\n" + chat_text
        )

        with self._db_ro_session() as session:
            system_prompt = self._system_prompt_repository_provider.get(session).get_system_prompt(channel_name)
        ai_messages = [AIMessage(role=Role.SYSTEM, content=system_prompt.prompt), AIMessage(role=Role.USER, content=prompt)]

        assistant_response = await self._llm_repository.generate_ai_response(ai_messages)
        assistant_message = assistant_response.message

        with self._unit_of_work_factory.create() as uow:
            uow.conversation_service.save_conversation_to_db(channel_name, prompt, assistant_message)

        data = json.loads(assistant_message)
        word = str(data.get("word", "")).strip()
        hint = str(data.get("hint", "")).strip()
        final_word = word.strip().lower()

        game = self.minigame_service.start_word_guess_game(channel_name, final_word, hint)
        with self._unit_of_work_factory.create() as uow:
            uow.add_used_words_use_case.add_used_words(channel_name, final_word)

        masked = game.get_masked_word()
        game_message = (
            f"НОВАЯ ИГРА 'поле чудес'! Слово из {len(game.target_word)} букв. Подсказка: {hint}. "
            f"Слово: {masked}. Приз: до {self.minigame_service.WORD_GAME_MAX_PRIZE} монет. "
            f"Угадывайте буквы: {self._prefix}{self._command_guess_letter} <буква> "
            f"или слово: {self._prefix}{self._command_guess_word} <слово>. "
            f"Время на игру: {self.minigame_service.WORD_GAME_DURATION_MINUTES} минут"
        )

        await self._send_channel_message(channel_name, game_message)

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name_lower(), content=game_message, current_time=datetime.utcnow()
            )

    async def _start_number_game(self, channel_name: str):
        game = self.minigame_service.start_guess_number_game(channel_name)
        game_message = (
            f"🎯 НОВАЯ МИНИ-ИГРА! Угадай число от {game.min_number} до {game.max_number}! "
            f"Первый, кто угадает, получит приз до {self.minigame_service.GUESS_GAME_PRIZE} монет! "
            f"Используй: {self._prefix}{self._command_guess} [число]. "
            f"Время на игру: {self.minigame_service.GUESS_GAME_DURATION_MINUTES} минут ⏰"
        )

        await self._send_channel_message(channel_name, game_message)
        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name_lower(), content=game_message, current_time=datetime.utcnow()
            )

    async def _start_rps_game(self, channel_name: str):
        self.minigame_service.start_rps_game(channel_name)
        game_message = (
            f"✊✌️🖐 НОВАЯ ИГРА КНБ! Банк старт: {MinigameService.RPS_BASE_BANK} монет + {MinigameService.RPS_ENTRY_FEE_PER_USER}"
            f" за каждого участника. "
            f"Участвовать: {self._prefix}{self._command_rps} <камень/ножницы/бумага> — "
            f"взнос {MinigameService.RPS_ENTRY_FEE_PER_USER} монет. "
            f"Время на голосование: {MinigameService.RPS_GAME_DURATION_MINUTES} минуты ⏰"
        )

        await self._send_channel_message(channel_name, game_message)
        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name_lower(), content=game_message, current_time=datetime.utcnow()
            )
