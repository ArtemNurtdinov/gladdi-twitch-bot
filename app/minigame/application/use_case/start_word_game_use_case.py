import json
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta

from app.ai.gen.conversation.domain.models import AIMessage, Role
from app.ai.gen.llm.domain.llm_repository import LLMRepository
from app.ai.gen.prompt.domain.system_prompt_repository import SystemPromptRepository
from app.minigame.application.uow.minigame_uow import MinigameUnitOfWorkFactory
from app.minigame.domain.minigame_service import MinigameService
from app.minigame.domain.model.word_guess import WordGuessGame
from core.provider import Provider
from core.types import SessionFactory


class StartWordGameUseCase:
    WORD_GAME_DURATION_MINUTES = 5
    WORD_GAME_MAX_PRIZE = 2000

    def __init__(
        self,
        minigame_service: MinigameService,
        prefix: str,
        minigame_uow: MinigameUnitOfWorkFactory,
        db_ro_session: SessionFactory,
        system_prompt_repository_provider: Provider[SystemPromptRepository],
        llm_repository: LLMRepository,
        command_guess_word: str,
        command_guess_letter: str,
        send_channel_message: Callable[[str, str], Awaitable[None]],
        bot_name: str,
    ):
        self._minigame_service = minigame_service
        self._minigame_uow = minigame_uow
        self._db_ro_session = db_ro_session
        self._system_prompt_repository_provider = system_prompt_repository_provider
        self._llm_repository = llm_repository
        self._prefix = prefix
        self._command_guess_word = command_guess_word
        self._command_guess_letter = command_guess_letter
        self._send_channel_message = send_channel_message
        self._bot_name = bot_name

    async def start(self, channel_name: str):
        with self._minigame_uow.create(read_only=True) as uow:
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

        with self._minigame_uow.create() as uow:
            uow.conversation_service.save_conversation_to_db(channel_name, prompt, assistant_message)

        data = json.loads(assistant_message)
        word = str(data.get("word", "")).strip()
        hint = str(data.get("hint", "")).strip()
        final_word = word.strip().lower()

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.WORD_GAME_DURATION_MINUTES)
        game = WordGuessGame(
            channel_name,
            word,
            hint,
            start_time,
            end_time,
            prize_amount=self.WORD_GAME_MAX_PRIZE,
            is_active=True,
            winner=None,
            winning_time=None,
            guessed_letters=set(),
        )

        self._minigame_service.save_word_gues_game(channel_name, game)

        with self._minigame_uow.create() as uow:
            uow.add_used_words_use_case.add_used_words(channel_name, final_word)

        masked = game.get_masked_word()
        game_message = (
            f"НОВАЯ ИГРА 'поле чудес'! Слово из {len(game.target_word)} букв. Подсказка: {hint}. "
            f"Слово: {masked}. Приз: до {self.WORD_GAME_MAX_PRIZE} монет. "
            f"Угадывайте буквы: {self._prefix}{self._command_guess_letter} <буква> "
            f"или слово: {self._prefix}{self._command_guess_word} <слово>. "
            f"Время на игру: {self.WORD_GAME_DURATION_MINUTES} минут"
        )

        await self._send_channel_message(channel_name, game_message)

        with self._minigame_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name, user_name=self._bot_name, content=game_message, current_time=datetime.utcnow()
            )
