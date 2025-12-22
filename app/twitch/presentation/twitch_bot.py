import asyncio
import logging
import random
import json
from typing import Coroutine, Any
from telegram.request import HTTPXRequest
from twitchio.ext import commands
from datetime import datetime, timedelta
import telegram

from app.ai.application.conversation_service import ConversationService
from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.ai.data.intent_detector_client import IntentDetectorClientImpl
from app.ai.data.llm_client import LLMClientImpl
from app.ai.data.message_repository import AIMessageRepositoryImpl
from app.battle.application.battle_use_case import BattleUseCase
from app.minigame.domain.models import RPS_CHOICES
from core.config import config
from collections import Counter

from core.db import db_ro_session, SessionLocal
from app.ai.domain.models import Intent, AIMessage, Role
from app.battle.data.battle_repository import BattleRepositoryImpl
from app.battle.domain.models import UserBattleStats
from app.betting.presentation.betting_schemas import UserBetStats
from app.betting.data.betting_repository import BettingRepositoryImpl
from app.betting.domain.betting_service import BettingService
from app.betting.domain.models import EmojiConfig, RarityLevel
from app.equipment.data.equipment_repository import EquipmentRepositoryImpl
from app.equipment.domain.equipment_service import EquipmentService
from app.minigame.data.db.word_history_repository import WordHistoryRepositoryImpl
from app.stream.domain.models import StreamStatistics
from app.twitch.infrastructure.twitch_api_service import TwitchApiService
from app.twitch.presentation.auth import TwitchAuth
from app.chat.application.chat_use_case import ChatUseCase
from app.chat.data.chat_repository import ChatRepositoryImpl
from app.joke.data.settings_repository import FileJokeSettingsRepository
from app.joke.domain.joke_service import JokeService
from app.economy.domain.economy_service import EconomyService
from app.economy.data.economy_repository import EconomyRepositoryImpl
from app.minigame.domain.minigame_service import MinigameService
from app.stream.domain.stream_service import StreamService
from app.stream.data.stream_repository import StreamRepositoryImpl
from app.viewer.data.viewer_repository import ViewerRepositoryImpl
from app.viewer.domain.viewer_session_service import ViewerTimeService
from app.economy.domain.models import ShopItems, TransactionType, JackpotPayoutMultiplierEffect, MissPayoutMultiplierEffect, \
    PartialPayoutMultiplierEffect

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
    SYSTEM_PROMPT_FOR_GROUP = (
        "Ты — GLaDDi, цифровой ассистент нового поколения."
        "\nТы обладаешь характером GLaDOS, но являешься искусственным интеллектом мужского пола."
        "\n\nИнформация о твоем создателе:"
        "\nИмя: Артем"
        "\nДата рождения: 04.12.1992"
        "\nПол: мужской"
        "\nНикнейм на twitch: ArtemNeFRiT"
        "\nОбщая информация: Более 10 лет опыта в разработке программного обеспечения. Увлекается AI и NLP. Любит играть в игры на ПК, иногда проводит стримы на Twitch."
        "\n- Twitch канал: https://www.twitch.tv/artemnefrit"
        "\n- Instagram: https://www.instagram.com/artem_nfrt/profilecard"
        "\n- Steam: https://steamcommunity.com/id/ArtNeFRiT"
        "\n- Telegram канал: https://t.me/artem_nefrit_gaming"
        "\n- Любимые игры: World of Warcraft, Cyberpunk 2077, Skyrim, CS2, Clair Obscur: Expedition 33"
        "\n\nТвоя задача — взаимодействие с чатом на Twitch. Модераторы канала: d3ar_88, voidterror. Vip-пользователи канала: dankar1000, gidrovlad, vrrrrrrredinka, rympelina"
        "\n\nОтвечай с юмором в стиле GLaDOS, не уступай, подкалывай, но оставайся полезным."
        "\nНе обсуждай политические темы, интим и криминал."
        "\nОтвечай кратко."
    )
    _COMMAND_ROLL = "ставка"
    _COMMAND_FOLLOWAGE = "followage"
    _COMMAND_GLADDI = "gladdi"
    _COMMAND_FIGHT = "битва"
    _COMMAND_BALANCE = "баланс"
    _COMMAND_BONUS = "бонус"
    _COMMAND_TRANSFER = "перевод"
    _COMMAND_SHOP = "магазин"
    _COMMAND_BUY = "купить"
    _COMMAND_EQUIPMENT = "экипировка"
    _COMMAND_TOP = "топ"
    _COMMAND_BOTTOM = "бомжи"
    _COMMAND_STATS = "стата"
    _COMMAND_GUESS = "угадай"
    _COMMAND_GUESS_LETTER = "буква"
    _COMMAND_GUESS_WORD = "слово"
    _COMMAND_RPS = "кнб"
    _COMMAND_HELP = "команды"
    _ROLL_COOLDOWN_SECONDS = 60
    _GROUP_ID = config.telegram.group_id
    _SOURCE_TWITCH = "twitch"
    _CHECK_VIEWERS_INTERVAL_SECONDS = 60

    def __init__(self, twitch_auth: TwitchAuth, twitch_api_service: TwitchApiService):
        self._prefix = '!'
        self.initial_channels = ['artemnefrit']
        super().__init__(token=twitch_auth.access_token, prefix=self._prefix, initial_channels=self.initial_channels)

        self._llm_client = LLMClientImpl()
        self._intent_detector = IntentDetectorClientImpl()
        self._intent_use_case = IntentUseCase(self._intent_detector, self._llm_client)
        self._prompt_service = PromptService()

        self.twitch_auth = twitch_auth
        self.twitch_api_service = twitch_api_service
        self.joke_service = JokeService(FileJokeSettingsRepository())
        self.stream_service = StreamService(StreamRepositoryImpl())
        self.equipment_service = EquipmentService(EquipmentRepositoryImpl())
        self.minigame_service = MinigameService(WordHistoryRepositoryImpl())
        self.viewer_service = ViewerTimeService(ViewerRepositoryImpl())

        self._restore_stream_context()

        self.battle_waiting_user: str | None = None
        self.current_stream_summaries = []
        self.last_chat_summary_time = None
        self.roll_cooldowns = {}
        self._tasks_started = False
        self._background_tasks: list[asyncio.Task] = []
        self._user_id_cache: dict[str, tuple[str, datetime]] = {}
        self._user_id_cache_ttl = timedelta(minutes=30)

        request = HTTPXRequest(connection_pool_size=10, pool_timeout=10)
        self.telegram_bot = telegram.Bot(token=config.telegram.bot_token, request=request)

        logger.info("Twitch бот инициализирован успешно")

    def _chat_use_case(self, db):
        return ChatUseCase(ChatRepositoryImpl(db))

    def _battle_use_case(self, db):
        return BattleUseCase(BattleRepositoryImpl(db))

    def _ai_conversation_use_case(self, db):
        message_repo = AIMessageRepositoryImpl(db)
        return ConversationService(message_repo)

    def _betting_service(self, db):
        return BettingService(BettingRepositoryImpl(db))

    def _economy_service(self, db):
        return EconomyService(EconomyRepositoryImpl(db))

    async def _get_user_id_cached(self, login: str) -> str | None:
        now = datetime.utcnow()
        cached = self._user_id_cache.get(login)
        if cached:
            cached_id, cached_at = cached
            if now - cached_at < self._user_id_cache_ttl:
                return cached_id

        user_info = await self.twitch_api_service.get_user_by_login(login)
        user_id = None if user_info is None else user_info.id
        if user_id:
            self._user_id_cache[login] = (user_id, now)
        return user_id

    async def _warmup_broadcaster_id(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст, пропускаем прогрев кеша ID")
                return

            channel_name = self.initial_channels[0]
            await self._get_user_id_cached(channel_name)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID канала: {e}")

    def _create_background_task(self, coro: Coroutine[Any, Any, Any]) -> asyncio.Task:
        task = asyncio.create_task(coro)
        self._background_tasks.append(task)

        def _cleanup(_task: asyncio.Task):
            if _task in self._background_tasks:
                self._background_tasks.remove(_task)

        task.add_done_callback(_cleanup)
        return task

    async def _start_background_tasks(self):
        if self._tasks_started:
            return

        self._create_background_task(self.post_joke_periodically())
        self._create_background_task(self.check_token_periodically())
        self._create_background_task(self.check_stream_start_periodically())
        self._create_background_task(self.summarize_chat_periodically())
        self._create_background_task(self.check_minigames_periodically())
        self._create_background_task(self.check_viewer_time_periodically())
        self._tasks_started = True

    async def close(self):
        for task in list(self._background_tasks):
            task.cancel()

        if self._background_tasks:
            await asyncio.gather(*self._background_tasks, return_exceptions=True)

        self._background_tasks.clear()
        self._tasks_started = False

        await super().close()

    async def event_ready(self):
        logger.info(f'Бот {self.nick} готов')
        if self.initial_channels:
            logger.info(f'Бот успешно подключен к каналу: {", ".join(self.initial_channels)}')
        else:
            logger.error('Проблемы с подключением к каналам!')
        await self._warmup_broadcaster_id()
        await self._start_background_tasks()

    async def event_channel_joined(self, channel):
        logger.info(f"Успешно подключились к каналу: {channel.name}")

    async def event_channel_join_failure(self, channel):
        logger.error(f"Не удалось подключиться к каналу {channel}")

    async def event_message(self, message):
        if not message.author:
            return
        nickname = message.author.display_name
        content = message.content
        channel_name = message.channel.name
        normalized_user_name = nickname.lower()

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, normalized_user_name, content, datetime.utcnow())
            self._economy_service(db).process_user_message_activity(channel_name, normalized_user_name)
            active_stream = self.stream_service.get_active_stream(db, channel_name)
            logger.info(f"Награда за активность: {nickname} получил {EconomyService.ACTIVITY_REWARD} монет")
            if active_stream:
                self.viewer_service.update_viewer_session(db, active_stream.id, channel_name, nickname.lower(), datetime.utcnow())

        if message.content.startswith(self._prefix):
            await self.handle_commands(message)
            return

        intent = self._intent_use_case.get_intent_from_text(message.content)
        logger.info(f"Определён интент: {intent}")

        prompt = None

        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(self._SOURCE_TWITCH, nickname, content)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(self._SOURCE_TWITCH, nickname, content)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(self._SOURCE_TWITCH, nickname, content)

        if prompt is not None:
            result = self.generate_response_in_chat(prompt, channel_name)
            await self._post_message_in_twitch_chat(result, message.channel)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            logger.info(f"Отправлен ответ на сообщение от {nickname}")

    @commands.command(name=_COMMAND_FOLLOWAGE)
    async def followage(self, ctx):
        if not ctx.author:
            return

        user_name = ctx.author.name
        channel_name = ctx.channel.name

        logger.info(f"Команда {self._COMMAND_FOLLOWAGE} от пользователя {user_name} в канале {channel_name}")

        broadcaster = await self.twitch_api_service.get_user_by_login(channel_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id

        if not broadcaster_id:
            logger.error(f"Не удалось получить ID канала {channel_name}")
            result = f'@{user_name}, произошла ошибка при получении информации о канале {channel_name}.'
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        user_id = ctx.author.id

        follow_info = await self.twitch_api_service.get_user_followage(broadcaster_id, str(user_id))

        if follow_info:
            followed_at = follow_info.followed_at
            follow_date = datetime.fromisoformat(followed_at[:-1])
            current_date = datetime.utcnow()
            follow_duration = current_date - follow_date

            days = follow_duration.days
            hours, remainder = divmod(follow_duration.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            logger.info(f"Пользователь {user_name} подписан на {days} дней, {hours} часов, {minutes} минут")
            prompt = f"@{user_name} отслеживает канал {channel_name} уже {days} дней, {hours} часов и {minutes} минут. Сообщи ему об этом как-нибудь оригинально."
            result = self.generate_response_in_chat(prompt, channel_name)
            with SessionLocal.begin() as db:
                self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
        else:
            result = f'@{user_name}, вы не отслеживаете канал {channel_name}.'
            logger.info(f"Пользователь {user_name} не подписан на канал {channel_name}")
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)

    @commands.command(name=_COMMAND_GLADDI)
    async def ask(self, ctx):
        channel_name = ctx.channel.name
        full_message = ctx.message.content
        question = full_message[len(f"{self._prefix}{self._COMMAND_GLADDI}"):].strip()
        nickname = ctx.author.display_name

        logger.info(f"Команда от пользователя {nickname}")

        intent = self._intent_use_case.get_intent_from_text(question)
        logger.info(f"Определён интент: {intent}")

        if intent == Intent.JACKBOX:
            prompt = self._prompt_service.get_jackbox_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self._prompt_service.get_skuf_femboy_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(self._SOURCE_TWITCH, nickname, question)
        else:
            prompt = self._prompt_service.get_default_prompt(self._SOURCE_TWITCH, nickname, question)

        result = self.generate_response_in_chat(prompt, channel_name)
        with SessionLocal.begin() as db:
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
        logger.info(f"Отправлен ответ пользователю {nickname}")
        await self._post_message_in_twitch_chat(result, ctx)

    @commands.command(name=_COMMAND_FIGHT)
    async def battle(self, ctx):
        channel_name = ctx.channel.name
        challenger = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_FIGHT} от пользователя {challenger}")

        fee = EconomyService.BATTLE_ENTRY_FEE

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, challenger)

        if user_balance.balance < fee:
            result = f"@{challenger}, недостаточно монет для участия в битве! Необходимо: {EconomyService.BATTLE_ENTRY_FEE} монет."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if not self.battle_waiting_user:
            with SessionLocal.begin() as db:
                user_balance = self._economy_service(db).subtract_balance(channel_name, challenger, fee,
                                                                          TransactionType.BATTLE_PARTICIPATION, "Участие в битве")
                if not user_balance:
                    error_result = f"@{challenger}, произошла ошибка при списании взноса за битву."
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), error_result, datetime.utcnow())

            if error_result:
                await ctx.send(error_result)
                return

            self.battle_waiting_user = challenger
            result = (
                f"@{challenger} ищет себе оппонента для эпичной битвы! Взнос: {EconomyService.BATTLE_ENTRY_FEE} монет. "
                f"Используй {self._prefix}{self._COMMAND_FIGHT}, чтобы принять вызов."
            )
            logger.info(f"{challenger} ищет оппонента для битвы")
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if self.battle_waiting_user == challenger:
            result = f"@{challenger}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            logger.warning(f"{challenger} пытается сражаться сам с собой")
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            challenger_balance = self._economy_service(db).subtract_balance(channel_name, challenger, fee,
                                                                            TransactionType.BATTLE_PARTICIPATION, "Участие в битве")
        if not challenger_balance:
            result = f"@{challenger}, произошла ошибка при списании взноса за битву."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        opponent = self.battle_waiting_user
        self.battle_waiting_user = None

        logger.info(f"Начинается битва между {opponent} и {challenger}")

        prompt = (
            f"На арене сражаются два героя: {opponent} и {challenger}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
        )

        with db_ro_session() as db:
            opponent_equipment = self.equipment_service.get_user_equipment(db, channel_name, opponent.lower())
            challenger_equipment = self.equipment_service.get_user_equipment(db, channel_name, challenger.lower())
            if opponent_equipment:
                equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in opponent_equipment]
                prompt += f"\nВооружение {opponent}: {', '.join(equipment_details)}."
            if challenger_equipment:
                equipment_details = [f"{item.shop_item.name} ({item.shop_item.description})" for item in challenger_equipment]
                prompt += f"\nВооружение {challenger}: {', '.join(equipment_details)}."

        winner = random.choice([opponent, challenger])
        loser = challenger if winner == opponent else opponent

        prompt += (
            "\nБитва должна быть короткой, но эпичной и красочной."
            f"\nПобедить в битве должен {winner}, проигравший: {loser}"
            f"\n\nПроигравший получит таймаут! Победитель получит {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        )

        result = self.generate_response_in_chat(prompt, channel_name)

        logger.info(f"Битва завершена. Победитель: {winner}")

        winner_amount = EconomyService.BATTLE_WINNER_PRIZE
        with SessionLocal.begin() as db:
            self._economy_service(db).add_balance(channel_name, winner, winner_amount, TransactionType.BATTLE_WIN,
                                                  f"Победа в битве против {loser}")
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            self._battle_use_case(db).save_battle_history(channel_name, opponent, challenger, winner, result)

        messages = self.split_text(result)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        logger.info(f"Проигравший: {loser}, получает таймаут")

        winner_message = f"{winner} получает {EconomyService.BATTLE_WINNER_PRIZE} монет!"
        await ctx.send(winner_message)

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), winner_message, datetime.utcnow())
        await asyncio.sleep(1)

        base_battle_timeout = 120
        with db_ro_session() as db:
            equipment = self.equipment_service.get_user_equipment(db, channel_name, loser.lower())
        final_timeout, protection_message = self.equipment_service.calculate_timeout_with_equipment(loser, base_battle_timeout, equipment)

        if final_timeout == 0:
            no_timeout_message = f"@{loser}, спасен от таймаута! {protection_message}"
            await ctx.send(no_timeout_message)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), no_timeout_message, datetime.utcnow())
        else:
            timeout_minutes = final_timeout // 60
            timeout_seconds_remainder = final_timeout % 60

            if timeout_minutes > 0:
                time_display = f"{timeout_minutes} минут" if timeout_seconds_remainder == 0 else f"{timeout_minutes}м {timeout_seconds_remainder}с"
            else:
                time_display = f"{timeout_seconds_remainder} секунд"

            reason = f"Поражение в битве! Время на тренировки: {time_display}"

            if protection_message:
                reason += f" {protection_message}"

            await self._timeout_user(ctx, loser, final_timeout, reason)

    @commands.command(name=_COMMAND_ROLL)
    async def roll(self, ctx, amount: str = None):
        channel_name = ctx.channel.name
        nickname = ctx.author.display_name

        bet_amount = BettingService.BET_COST
        if amount:
            try:
                bet_amount = int(amount)
            except ValueError:
                result = (
                    f"@{nickname}, неверная сумма ставки! Используй: {self._prefix}{self._COMMAND_ROLL} [сумма] (например: {self._prefix}{self._COMMAND_ROLL} 100). "
                    f"Диапазон: {BettingService.MIN_BET_AMOUNT}-{BettingService.MAX_BET_AMOUNT} монет.")
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
                return

        logger.info(f"Команда {self._COMMAND_ROLL} от пользователя {nickname}, сумма ставки: {bet_amount}")

        current_time = datetime.now()
        with db_ro_session() as db:
            equipment = self.equipment_service.get_user_equipment(db, channel_name, nickname.lower())
            cooldown_seconds = self.equipment_service.calculate_roll_cooldown_seconds(self._ROLL_COOLDOWN_SECONDS, equipment)

        if nickname in self.roll_cooldowns:
            time_since_last = (current_time - self.roll_cooldowns[nickname]).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{nickname}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                logger.info(f"Пользователь {nickname} попытался использовать команду в кулдауне. Осталось: {remaining_time:.0f} сек")
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
                return

        self.roll_cooldowns[nickname] = current_time
        logger.debug(f"Обновлен кулдаун для пользователя {nickname}: {current_time}")

        emojis = EmojiConfig.get_emojis_list()
        weights = EmojiConfig.get_weights_list()

        slot_results = random.choices(emojis, weights=weights, k=3)
        slot_result_string = EmojiConfig.format_slot_result(slot_results)

        logger.info(f"Результат слот-машины для {nickname}: {slot_result_string}")

        unique_results = set(slot_results)

        if len(unique_results) == 1:
            result_type = "jackpot"
        elif len(unique_results) == 2:
            result_type = "partial"
        else:
            result_type = "miss"

        normalized_user_name = nickname.lower()

        if bet_amount < BettingService.MIN_BET_AMOUNT:
            result = f"Минимальная сумма ставки: {BettingService.MIN_BET_AMOUNT} монет."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if bet_amount > BettingService.MAX_BET_AMOUNT:
            result = f"Максимальная сумма ставки: {BettingService.MAX_BET_AMOUNT} монет."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with db_ro_session() as db:
            rarity_level = self._betting_service(db).determine_correct_rarity(slot_result_string, result_type)
            equipment = self.equipment_service.get_user_equipment(db, channel_name, normalized_user_name)

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).subtract_balance(
                channel_name,
                normalized_user_name,
                bet_amount,
                TransactionType.BET_LOSS,
                f"Ставка в слот-машине: {slot_result_string}"
            )
            if not user_balance:
                result = f"Недостаточно средств для ставки! Необходимо: {bet_amount} монет."
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
                await ctx.send(result)
                return
            base_payout = BettingService.RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
            timeout_seconds = None
            if result_type == "jackpot":
                payout = base_payout * BettingService.JACKPOT_MULTIPLIER
            elif result_type == "partial":
                payout = base_payout * BettingService.PARTIAL_MULTIPLIER
            else:
                consolation_prize = BettingService.CONSOLATION_PRIZES.get(rarity_level, 0)
                if consolation_prize > 0:
                    payout = max(consolation_prize, bet_amount * 0.1)
                    if rarity_level in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                        timeout_seconds = 0
                    elif rarity_level == RarityLevel.EPIC:
                        timeout_seconds = 60
                    else:
                        timeout_seconds = 120
                else:
                    payout = 0
                    timeout_seconds = 180

            if payout > 0:
                if result_type in ("jackpot", "partial"):
                    jackpot_multiplier = 1.0
                    partial_multiplier = 1.0
                    for item in equipment:
                        for effect in item.shop_item.effects:
                            if isinstance(effect, JackpotPayoutMultiplierEffect) and result_type == "jackpot":
                                jackpot_multiplier *= effect.multiplier
                            if isinstance(effect, PartialPayoutMultiplierEffect) and result_type == "partial":
                                partial_multiplier *= effect.multiplier
                    if result_type == "jackpot" and jackpot_multiplier != 1.0:
                        payout *= jackpot_multiplier
                    if result_type == "partial" and partial_multiplier != 1.0:
                        payout *= partial_multiplier
                elif result_type == "miss":
                    miss_multiplier = 1.0
                    for item in equipment:
                        for effect in item.shop_item.effects:
                            if isinstance(effect, MissPayoutMultiplierEffect):
                                miss_multiplier *= effect.multiplier
                    if miss_multiplier != 1.0:
                        payout *= miss_multiplier

            payout = int(payout) if payout > 0 else 0

            if payout > 0:
                transaction_type = TransactionType.BET_WIN if result_type != "miss" else TransactionType.BET_WIN
                description = f"Выигрыш в слот-машине: {slot_result_string}" if result_type != "miss" else f"Консольный приз: {slot_result_string}"
                user_balance = self._economy_service(db).add_balance(channel_name, normalized_user_name, payout, transaction_type,
                                                                     description)
            self._betting_service(db).save_bet(channel_name, normalized_user_name, slot_result_string, result_type, rarity_level)

        result_emoji = self.get_result_emoji(result_type, payout)

        economic_info = f" {result_emoji} Баланс: {user_balance.balance} монет"

        profit = payout - bet_amount

        profit_display = self.get_profit_display(result_type, payout, profit)

        economic_info += f" ({profit_display})"

        final_result = f"{slot_result_string} {economic_info}"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), final_result, datetime.utcnow())

        messages = self.split_text(final_result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        if timeout_seconds is not None and timeout_seconds > 0:
            base_timeout_duration = timeout_seconds if timeout_seconds else 0

            with db_ro_session() as db:
                equipment = self.equipment_service.get_user_equipment(db, channel_name, nickname.lower())
            final_timeout, protection_message = self.equipment_service.calculate_timeout_with_equipment(
                nickname,
                base_timeout_duration,
                equipment
            )

            if final_timeout == 0:
                if self.is_consolation_prize(result_type, payout):
                    no_timeout_message = f"🎁 @{nickname}, {protection_message} Консольный приз: {payout} монет"
                else:
                    no_timeout_message = f"🛡️ @{nickname}, {protection_message}"

                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), no_timeout_message, datetime.utcnow())

                messages = self.split_text(no_timeout_message)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)
            else:
                if self.is_consolation_prize(result_type, payout):
                    reason = f"Промах с редким эмодзи! Консольный приз: {payout} монет. Таймаут: {final_timeout} сек ⏰"
                else:
                    reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                messages = self.split_text(reason)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)

                await self._timeout_user(ctx, nickname, final_timeout, reason)
        elif self.is_miss(result_type):
            if self.is_consolation_prize(result_type, payout):
                no_timeout_message = f"🎁 @{nickname}, повезло! Редкий эмодзи спас от таймаута! Консольный приз: {payout} монет"
            else:
                no_timeout_message = f"✨ @{nickname}, редкий эмодзи спас от таймаута!"

            messages = self.split_text(no_timeout_message)
            for msg in messages:
                await ctx.send(msg)
                await asyncio.sleep(0.3)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), no_timeout_message, datetime.utcnow())

        self._cleanup_old_cooldowns()

    def is_miss(self, result_type: str) -> bool:
        return result_type == "miss"

    def is_consolation_prize(self, result_type: str, payout: int) -> bool:
        return self.is_miss(result_type) and payout > 0

    def is_jackpot(self, result_type: str) -> bool:
        return result_type == "jackpot"

    def is_partial_match(self, result_type: str) -> bool:
        return result_type == "partial"

    def get_result_emoji(self, result_type: str, payout: int) -> str:
        if self.is_consolation_prize(result_type, payout):
            return "🎁"
        elif self.is_jackpot(result_type):
            return "🎰"
        elif self.is_partial_match(result_type):
            return "✨"
        elif self.is_miss(result_type):
            return "💥"
        else:
            return "💰"

    def get_profit_display(self, result_type: str, payout: int, profit: int) -> str:
        if self.is_consolation_prize(result_type, payout):
            net_result = profit
            if net_result > 0:
                return f"+{net_result}"
            elif net_result < 0:
                return f"{net_result}"
            else:
                return "±0"
        else:
            if profit > 0:
                return f"+{profit}"
            elif profit < 0:
                return f"{profit}"
            else:
                return "±0"

    @commands.command(name=_COMMAND_BALANCE)
    async def balance(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_BALANCE} от пользователя {user_name}")

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, user_name)

        result = f"💰 @{user_name}, твой баланс: {user_balance.balance} монет"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

    @commands.command(name=_COMMAND_BONUS)
    async def daily_bonus(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_BONUS} от пользователя {user_name}")

        with db_ro_session() as db:
            active_stream = self.stream_service.get_active_stream(db, channel_name)

        if not active_stream:
            result = f"🚫 @{user_name}, бонус доступен только во время стрима!"
        else:
            with SessionLocal.begin() as db:
                user_equipment = self.equipment_service.get_user_equipment(db, channel_name, user_name.lower())
                bonus_result = self._economy_service(db).claim_daily_bonus(active_stream.id, channel_name, user_name.lower(),
                                                                           user_equipment)
                if bonus_result.success:
                    if bonus_result.bonus_message:
                        result = f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! Баланс: {bonus_result.user_balance.balance} монет. {bonus_result.bonus_message}"
                    else:
                        result = f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! Баланс: {bonus_result.user_balance.balance} монет"
                else:
                    if bonus_result.failure_reason == "already_claimed":
                        result = f"⏰ @{user_name}, бонус уже получен на этом стриме!"
                    elif bonus_result.failure_reason == "error":
                        result = f"❌ @{user_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                    else:
                        result = f"❌ @{user_name}, бонус недоступен!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_TRANSFER)
    async def transfer_money(self, ctx, recipient: str = None, amount: str = None):
        channel_name = ctx.channel.name
        sender_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_TRANSFER} от пользователя {sender_name}")

        if not recipient or not amount:
            result = f"@{sender_name}, используй: {self._prefix}{self._COMMAND_TRANSFER} [никнейм] [сумма]. Например: {self._prefix}{self._COMMAND_TRANSFER} @ArtemNeFRiT 100"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            transfer_amount = int(amount)
        except ValueError:
            result = f"@{sender_name}, неверная сумма! Укажи число. Например: {self._prefix}{self._COMMAND_TRANSFER} {recipient} 100"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if transfer_amount <= 0:
            result = f"@{sender_name}, сумма должна быть больше 0!"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        recipient = recipient.lstrip('@')

        normalized_sender_name = sender_name.lower()
        normalized_receiver_name = recipient.lower()

        with SessionLocal.begin() as db:
            transfer_result = self._economy_service(db).transfer_money(channel_name, normalized_sender_name, normalized_receiver_name,
                                                                       transfer_amount)
        logger.info(f"Перевод выполнен: {sender_name} -> {recipient}")

        if transfer_result.success:
            result = f"@{sender_name} перевел {transfer_amount} монет пользователю @{recipient}! "
        else:
            result = f"@{sender_name}, {transfer_result.message}"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

    @commands.command(name=_COMMAND_SHOP)
    async def shop(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_SHOP} от пользователя {user_name}")

        all_items = ShopItems.get_all_items()

        result = "МАГАЗИН АРТЕФАКТОВ:\n"

        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        for item_type, item in sorted_items:
            result += f"{item.emoji} {item.name} - {item.price} монет. "

        result += f"Используй: {self._prefix}{self._COMMAND_BUY} [название предмета]. Пример: {self._prefix}{self._COMMAND_BUY} стул. Все предметы действуют 30 дней!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_BUY)
    async def buy_item(self, ctx, *, item_name: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_BUY} от пользователя {user_name}")

        if not item_name:
            result = f"@{user_name}, укажи название предмета! Используй: {self._prefix}{self._COMMAND_BUY} [название]. Пример: {self._prefix}{self._COMMAND_BUY} стул"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            item_type = ShopItems.find_item_by_name(item_name)
        except ValueError as e:
            result = str(e)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        item = ShopItems.get_item(item_type)

        normalized_user_name = user_name.lower()
        with db_ro_session() as db:
            equipment_exists = self.equipment_service.equipment_exists(db, channel_name, normalized_user_name, item_type)

        if equipment_exists:
            result = f"У вас уже есть {item.name}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).get_user_balance(channel_name, normalized_user_name)

        if user_balance.balance < item.price:
            result = f"Недостаточно монет! Нужно {item.price}, у вас {user_balance.balance}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        with SessionLocal.begin() as db:
            self._economy_service(db).subtract_balance(channel_name, normalized_user_name, item.price, TransactionType.SHOP_PURCHASE,
                                                       f"Покупка '{item.name}'")
            self.equipment_service.add_equipment_to_user(db, channel_name, normalized_user_name, item_type)

        result = f"@{user_name} купил {item.emoji} '{item.name}' за {item.price} монет!"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
        await ctx.send(result)

    @commands.command(name=_COMMAND_EQUIPMENT)
    async def equipment(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        normalized_user_name = user_name.lower()

        logger.info(f"Команда {self._COMMAND_EQUIPMENT} от пользователя {user_name}")

        with db_ro_session() as db:
            equipment = self.equipment_service.get_user_equipment(db, channel_name, normalized_user_name)

        if not equipment:
            result = f"@{user_name}, у вас нет активной экипировки. Загляните в {self._prefix}{self._COMMAND_SHOP}!"
        else:
            result = f"Экипировка @{user_name}:\n"

            for item in equipment:
                expires_date = item.expires_at.strftime("%d.%m.%Y")
                result += f"{item.shop_item.emoji} {item.shop_item.name} до {expires_date}\n"

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_TOP)
    async def top_users(self, ctx):
        channel_name = ctx.channel.name

        logger.info(f"Команда {self._COMMAND_TOP}")

        with db_ro_session() as db:
            top_users = self._economy_service(db).get_top_users(channel_name, limit=7)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            result = "ТОП БОГАЧЕЙ:\n"
            for i, user in enumerate(top_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_BOTTOM)
    async def bottom_users(self, ctx):
        channel_name = ctx.channel.name

        logger.info(f"Команда {self._COMMAND_BOTTOM}")

        with db_ro_session() as db:
            bottom_users = self._economy_service(db).get_bottom_users(channel_name, limit=10)

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            result = "💸 ТОП БОМЖЕЙ:\n"
            for i, user in enumerate(bottom_users, 1):
                result += f"{i}. {user.user_name}: {user.balance} монет."

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_HELP)
    async def list_commands(self, ctx):
        channel_name = ctx.channel.name
        prefix = self._prefix
        help_text = (
            "📜 Доступные команды: "
            f"{prefix}{self._COMMAND_BALANCE}: ваш баланс. "
            f"{prefix}{self._COMMAND_BONUS}: ежедневный бонус. "
            f"{prefix}{self._COMMAND_ROLL} [сумма]: слот-машина. "
            f"{prefix}{self._COMMAND_TRANSFER} @ник сумма: перевод монет. "
            f"{prefix}{self._COMMAND_SHOP}: магазин артефактов. "
            f"{prefix}{self._COMMAND_BUY} название: купить предмет. "
            f"{prefix}{self._COMMAND_EQUIPMENT}: ваша экипировка. "
            f"{prefix}{self._COMMAND_TOP}: топ богачей. "
            f"{prefix}{self._COMMAND_BOTTOM}: топ бомжей. "
            f"{prefix}{self._COMMAND_STATS}: ваша стата. "
            f"{prefix}{self._COMMAND_FIGHT}: сразиться в битве. "
            f"{prefix}{self._COMMAND_GLADDI} текст: спросить GLaDDi. "
            f"{prefix}{self._COMMAND_FOLLOWAGE}: сколько подписан. "
        )

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), help_text, datetime.utcnow())

        messages = self.split_text(help_text)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_STATS)
    async def user_stats(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_STATS} от пользователя {user_name}")

        normalized_user_name = user_name.lower()

        with SessionLocal.begin() as db:
            balance = self._economy_service(db).get_user_balance(channel_name, normalized_user_name)
            bets = self._betting_service(db).get_user_bets(channel_name, normalized_user_name)

        if not bets:
            bet_stats = UserBetStats(total_bets=0, jackpots=0, jackpot_rate=0)
        else:
            total_bets = len(bets)
            jackpots = sum(1 for bet in bets if bet.result_type == "jackpot")
            jackpot_rate = (jackpots / total_bets) * 100 if total_bets > 0 else 0

            bet_stats = UserBetStats(total_bets=total_bets, jackpots=jackpots, jackpot_rate=jackpot_rate)

        with db_ro_session() as db:
            battles = self._battle_use_case(db).get_user_battles(channel_name, user_name)

        if not battles:
            battle_stats = UserBattleStats(total_battles=0, wins=0, losses=0, win_rate=0.0)
        else:
            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == user_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0
            battle_stats = UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)

        result = f"📊 Статистика @{user_name}: "
        result += f" 💰 Баланс: {balance.balance} монет."

        if bet_stats.total_bets > 0:
            result += f" 🎰 Ставки: {bet_stats.total_bets} | Джекпоты: {bet_stats.jackpots} ({bet_stats.jackpot_rate:.1f}%). "

        if battle_stats.has_battles():
            result += f" ⚔️ Битвы: {battle_stats.total_battles} | Побед: {battle_stats.wins} ({battle_stats.win_rate:.1f}%). "

        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_GUESS)
    async def guess_number(self, ctx, number: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_GUESS} от пользователя {user_name}, число: {number}")
        if not number:
            result = f"@{user_name}, используй: {self._prefix}{self._COMMAND_GUESS} [число]"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        try:
            guess = int(number)
        except ValueError:
            result = f"@{user_name}, укажи правильное число! Например: {self._prefix}{self._COMMAND_GUESS} 42"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if not self.minigame_service.is_game_active(channel_name):
            result = "Сейчас нет активной игры 'угадай число'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        game = self.minigame_service.get_active_game(channel_name)

        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_guess_game_timeout(channel_name)
            result = f"Время игры истекло! Загаданное число было {game.target_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if not game.is_active:
            result = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if not game.min_number <= guess <= game.max_number:
            result = f"Число должно быть от {game.min_number} до {game.max_number}"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
            return

        if guess == game.target_number:
            self.minigame_service.finish_game_with_winner(game, channel_name, user_name, guess)
            description = f"Победа в игре 'угадай число': {guess}"
            message = f"ПОЗДРАВЛЯЕМ! @{user_name} угадал число {guess} и выиграл {game.prize_amount} монет!"

            with SessionLocal.begin() as db:
                self._economy_service(db).add_balance(channel_name, user_name, game.prize_amount, TransactionType.MINIGAME_WIN, description)
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - MinigameService.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            message = f"@{user_name}, не угадал! Загаданное число {hint} {guess}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)

    @commands.command(name=_COMMAND_GUESS_LETTER)
    async def guess_letter(self, ctx, letter: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not letter:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), status, datetime.utcnow())
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return

        if not self.minigame_service.is_word_game_active(channel_name):
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        if not len(letter) == 1 or not letter.isalpha():
            message = "Введите одну букву русского алфавита"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        letter_revealed = False

        letter = letter.lower()
        if letter in game.guessed_letters:
            letter_revealed = False
        if letter in game.target_word:
            game.guessed_letters.add(letter)
            letter_revealed = True

        masked = game.get_masked_word()

        if letter_revealed:
            if game.prize_amount > MinigameService.WORD_GAME_MIN_PRIZE:
                game.prize_amount = max(MinigameService.WORD_GAME_MIN_PRIZE,
                                        game.prize_amount - MinigameService.WORD_GAME_LETTER_REWARD_DECREASE)
            letters_in_word = {ch for ch in game.target_word if ch.isalpha()}
            all_letters_revealed = letters_in_word.issubset(game.guessed_letters)
            if all_letters_revealed:
                self.minigame_service.finish_word_game_with_winner(game, channel_name, user_name)
                normalized_user_name = user_name.lower()

                with SessionLocal.begin() as db:
                    winner_balance = self._economy_service(db).add_balance(channel_name, normalized_user_name, game.prize_amount,
                                                                           TransactionType.MINIGAME_WIN, f"Победа в игре 'поле чудес'")

                message = f"ПОЗДРАВЛЯЕМ! @{user_name} угадал слово '{game.target_word}' и выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
                self.minigame_service.finish_word_game_with_winner(game, channel_name, user_name)
            else:
                message = f"Буква есть! Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
        else:
            message = f"Такой буквы нет. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)

    @commands.command(name=_COMMAND_GUESS_WORD)
    async def guess_word(self, ctx, *, word: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not word:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                with SessionLocal.begin() as db:
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), status, datetime.utcnow())
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return

        word_game_is_active = self.minigame_service.is_word_game_active(channel_name)
        if not word_game_is_active:
            message = "Сейчас нет активной игры 'поле чудес'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        game = self.minigame_service.get_active_word_game(channel_name)
        if datetime.utcnow() > game.end_time:
            self.minigame_service.finish_word_game_timeout(channel_name)
            message = f"Время игры истекло! Слово было '{game.target_word}'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        if word.strip().lower() == game.target_word:
            self.minigame_service.finish_word_game_with_winner(game, channel_name, user_name)
            normalized_user_name = user_name.lower()

            with SessionLocal.begin() as db:
                winner_balance = self._economy_service(db).add_balance(channel_name, normalized_user_name, game.prize_amount,
                                                                       TransactionType.MINIGAME_WIN, f"Победа в игре 'поле чудес'")

            message = f"ПОЗДРАВЛЯЕМ! @{user_name} угадал слово '{game.target_word}' и выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
        else:
            masked = game.get_masked_word()
            message = f"Неверное слово. Слово: {masked}."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)

    @commands.command(name=_COMMAND_RPS)
    async def join_rps(self, ctx, choice: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not choice:
            await ctx.send(f"@{user_name}, укажите ваш выбор: камень / ножницы / бумага")
            return

        rps_game_is_active = self.minigame_service.rps_game_is_active(channel_name)
        if not rps_game_is_active:
            message = "Сейчас нет активной игры 'камень-ножницы-бумага'"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        game = self.minigame_service.get_active_rps_game(channel_name)

        if datetime.utcnow() > game.end_time:
            bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game)
            if winners:
                share = max(1, game.bank // len(winners))
                with SessionLocal.begin() as db:
                    for winner in winners:
                        self._economy_service(db).add_balance(channel_name, winner, share, TransactionType.MINIGAME_WIN,
                                                              f"Победа в КНБ ({winning_choice})")
                winners_display = ", ".join(f"@{winner}" for winner in winners)
                message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
            else:
                message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        if not game.is_active:
            message = "Игра уже завершена"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        normalized_choice = choice.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            message = "Выберите: камень, ножницы или бумага"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        normalized_user_name = user_name.lower()
        if game.user_choices[normalized_user_name]:
            existing = game.user_choices[normalized_user_name]
            message = f"Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        fee = MinigameService.RPS_ENTRY_FEE_PER_USER

        with SessionLocal.begin() as db:
            user_balance = self._economy_service(db).subtract_balance(channel_name, user_name, fee, TransactionType.SPECIAL_EVENT,
                                                                      "Участие в игре 'камень-ножницы-бумага'")
        if not user_balance:
            message = f"Недостаточно средств! Требуется {fee} монет"
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
            await ctx.send(message)
            return

        game.bank += fee
        game.user_choices[normalized_user_name] = choice

        message = f"Принято: @{user_name} — {normalized_choice}"
        with SessionLocal.begin() as db:
            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
        await ctx.send(message)

    def _cleanup_old_cooldowns(self):
        current_time = datetime.now()
        cleanup_threshold = 300

        old_nicknames = []
        for nickname, last_time in self.roll_cooldowns.items():
            if (current_time - last_time).total_seconds() > cleanup_threshold:
                old_nicknames.append(nickname)

        for nickname in old_nicknames:
            del self.roll_cooldowns[nickname]

        total_cleaned = len(old_nicknames)
        if total_cleaned > 0:
            logger.debug(f"Очищено {total_cleaned} старых записей кулдаунов: roll={len(old_nicknames)}")

    async def _timeout_user(self, ctx, username: str, duration_seconds: int, reason: str):
        try:
            channel_name = ctx.channel.name

            user = await self.twitch_api_service.get_user_by_login(username)
            user_id = None if user is None else user.id

            broadcaster_id = await self._get_user_id_cached(channel_name)
            moderator_id = await self._get_user_id_cached(self.nick)

            if not user_id:
                logger.error(f"Не удалось получить ID пользователя {username}")
                return
            if not broadcaster_id:
                logger.error(f"Не удалось получить ID канала {channel_name}")
                return
            if not moderator_id:
                logger.error(f"Не удалось получить ID модератора {self.nick}")
                return

            success = await self.twitch_api_service.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)

            if not success:
                raise Exception("Не удалось применить таймаут")
        except Exception as e:
            logger.error(f"Ошибка при попытке дать таймаут пользователю {username}: {e}")

    def split_text(self, text, max_length=500):
        if len(text) <= max_length:
            return [text]

        messages = []
        while text:
            if len(text) <= max_length:
                messages.append(text)
                break

            split_pos = text.rfind(' ', 0, max_length)

            if split_pos == -1:
                split_pos = max_length

            part = text[:split_pos].strip()
            if part:
                messages.append(part)

            text = text[split_pos:].strip()
        return messages

    async def _post_message_in_twitch_chat(self, message: str, ctx):
        messages = self.split_text(message)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def post_joke_periodically(self):
        logger.info("Запуск периодической генерации анекдотов")
        while True:
            await asyncio.sleep(30)

            if not self.joke_service.should_generate_jokes():
                continue

            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст в post_joke_periodically. Пропускаем генерацию анекдота.")
                    continue

                channel_name = self.initial_channels[0]
                broadcaster_id = await self._get_user_id_cached(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name} для генерации анекдота")
                    continue

                stream_info = await self.twitch_api_service.get_stream_info(broadcaster_id)
                prompt = f"Придумай анекдот, связанной с категорией трансляции: {stream_info.game_name}."
                result = self.generate_response_in_chat(prompt, channel_name)
                with SessionLocal.begin() as db:
                    self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
                    self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
                channel = self.get_channel(channel_name)
                await channel.send(result)
                logger.info(f"Анекдот сгенерирован: {result}")
                self.joke_service.mark_joke_generated()
            except Exception as e:
                logger.error(f"Ошибка при генерации анекдота: {e}")
                await asyncio.sleep(60)

    async def check_token_periodically(self):
        logger.info("Запуск периодической проверки токена")
        while True:
            await asyncio.sleep(1000)
            token_is_valid = self.twitch_auth.check_token_is_valid()
            logger.info(f"Статус токена: {'действителен' if token_is_valid else 'недействителен'}")
            if not token_is_valid:
                self.twitch_auth.update_access_token()
                logger.info("Токен обновлён")

    async def check_stream_start_periodically(self):
        logger.info("Запуск периодической проверки статуса стрима")

        while True:
            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст. Ожидание...")
                    await asyncio.sleep(60)
                    continue

                channel_name = self.initial_channels[0]
                broadcaster_id = await self._get_user_id_cached(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name}. Пропускаем проверку.")
                    await asyncio.sleep(60)
                    continue

                with db_ro_session() as db:
                    active_stream = self.stream_service.get_active_stream(db, channel_name)

                stream_status = await self.twitch_api_service.get_stream_status(broadcaster_id)

                if stream_status is None:
                    logger.error(f"Не удалось получить статус стрима для канала {channel_name}")
                    await asyncio.sleep(60)
                    continue

                game_name = None
                title = None
                if stream_status.is_online and stream_status.stream_data:
                    game_name = stream_status.stream_data.game_name
                    title = stream_status.stream_data.title

                if stream_status.is_online and active_stream is None:
                    logger.info(f"Стрим начался: {game_name} - {title}")

                    try:
                        started_at = datetime.utcnow()
                        with SessionLocal.begin() as db:
                            self.stream_service.start_new_stream(db, channel_name, started_at, game_name, title)
                        self.minigame_service.set_stream_start_time(channel_name, started_at)
                        await self.stream_announcement(game_name, title, channel_name)
                        self.current_stream_summaries = []
                    except Exception as e:
                        logger.error(f"Ошибка при создании стрима: {e}")

                elif not stream_status.is_online and active_stream is not None:
                    logger.info("Стрим завершён")
                    finish_time = datetime.utcnow()

                    with SessionLocal.begin() as db:
                        self.stream_service.end_stream(db, active_stream.id, finish_time)
                        self.viewer_service.finish_stream_sessions(db, active_stream.id, finish_time)
                        total_viewers = self.viewer_service.get_unique_viewers_count(db, active_stream.id)
                        self.stream_service.update_stream_total_viewers(db, active_stream.id, total_viewers)
                        logger.info(f"Стрим завершен в БД: ID {active_stream.id}")

                    self.minigame_service.reset_stream_state(channel_name)

                    with db_ro_session() as db:
                        chat_messages = self._chat_use_case(db).get_chat_messages(channel_name, active_stream.started_at, finish_time)
                        total_messages = len(chat_messages)
                        unique_users = len(set(msg.user_name for msg in chat_messages))
                        user_counts = Counter(msg.user_name for msg in chat_messages)

                    if user_counts:
                        top_user = user_counts.most_common(1)[0][0]
                    else:
                        top_user = None

                    with db_ro_session() as db:
                        battles = self._battle_use_case(db).get_battles(channel_name, active_stream.started_at)

                    total_battles = len(battles)
                    if battles:
                        winner_counts = Counter(b.winner for b in battles)
                        top_winner = winner_counts.most_common(1)[0][0]
                    else:
                        top_winner = None
                    stats = StreamStatistics(total_messages, unique_users, top_user, total_battles, top_winner)

                    try:
                        await self.stream_summarize(stats, channel_name, active_stream.started_at, finish_time)
                    except Exception as e:
                        logger.error(f"Ошибка при вызове stream_summarize: {e}")

                elif stream_status.is_online and active_stream:
                    if active_stream.game_name != game_name or active_stream.title != title:
                        with SessionLocal.begin() as db:
                            self.stream_service.update_stream_metadata(db, active_stream.id, game_name, title)
                        logger.info(f"Обновлены метаданные стрима: игра='{game_name}', название='{title}'")

            except Exception as e:
                logger.error(f"Ошибка в check_stream_start_periodically: {e}")

            await asyncio.sleep(60)

    async def stream_announcement(self, game_name: str, title: str, channel_name: str):
        prompt = f"Начался стрим. Категория: {game_name}, название: {title}. Сгенерируй краткий анонс для телеграм канала. Ссылка на трансляцию: https://twitch.tv/artemnefrit"
        result = self.generate_response_in_chat(prompt, channel_name)
        try:
            await self.telegram_bot.send_message(chat_id=self._GROUP_ID, text=result)
            with SessionLocal.begin() as db:
                self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            logger.info(f"Анонс стрима отправлен в Telegram: {result}")
        except Exception as e:
            logger.error(f"Ошибка отправки анонса в Telegram: {e}")

    async def stream_summarize(self, stream_stat: StreamStatistics, channel_name: str, stream_start_dt, stream_end_dt):
        logger.info("Создание итогового отчёта о стриме")

        if self.last_chat_summary_time is None:
            self.last_chat_summary_time = stream_start_dt

        with db_ro_session() as db:
            last_messages = self._chat_use_case(db).get_chat_messages(channel_name, self.last_chat_summary_time, stream_end_dt)
            if last_messages:
                chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
                prompt = (
                    f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                    f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
                )
                result = self.generate_response_in_chat(prompt, channel_name)
                self.current_stream_summaries.append(result)

        duration = stream_end_dt - stream_start_dt
        hours, remainder = divmod(int(duration.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        duration_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        top_user = stream_stat.top_user if stream_stat.top_user else 'нет'

        stream_stat_message = f"Длительность: {duration_str}. Сообщений: {stream_stat.total_messages}. Самый активный пользователь: {top_user}."

        if stream_stat.total_battles > 0:
            stream_stat_message += f" Битв за стрим: {stream_stat.total_battles}. Главный победитель: {stream_stat.top_winner}"

        if top_user and top_user != 'нет':
            reward_amount = 200
            with SessionLocal.begin() as db:
                user_balance = self._economy_service(db).add_balance(channel_name, top_user, reward_amount, TransactionType.SPECIAL_EVENT,
                                                                     "Награда за самую высокую активность в стриме")
                stream_stat_message += f"{top_user} получает награду {reward_amount} монет за активность! Баланс: {user_balance.balance} монет."

        logger.info(f"Статистика стрима: {stream_stat_message}")

        prompt = f"Трансляция была завершена. Статистика:\n{stream_stat_message}"

        if self.current_stream_summaries:
            summary_text = "\n".join(self.current_stream_summaries)
            prompt += f"\n\nВыжимки из того, что происходило в чате: {summary_text}"

        prompt += f"\n\nНа основе предоставленной информации подведи краткий итог трансляции"
        result = self.generate_response_in_chat(prompt, channel_name)

        with SessionLocal.begin() as db:
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)

        self.current_stream_summaries = []
        self.last_chat_summary_time = None

        await self.telegram_bot.send_message(chat_id=self._GROUP_ID, text=result)

    async def summarize_chat_periodically(self):
        logger.info("Запуск периодического анализа чата")
        while True:
            await asyncio.sleep(20 * 60)

            if not self.initial_channels:
                logger.warning("Список каналов пуст в summarize_chat_periodically. Пропускаем анализ чата.")
                continue

            channel_name = self.initial_channels[0]
            try:
                broadcaster_id = await self._get_user_id_cached(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name} для анализа чата")
                    continue

                with db_ro_session() as db:
                    active_stream = self.stream_service.get_active_stream(db, channel_name)
                if not active_stream:
                    logger.debug("Стрим не активен, пропускаем анализ чата")
                    continue
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса стрима в summarize_chat_periodically: {e}")
                continue

            since = datetime.utcnow() - timedelta(minutes=20)
            with db_ro_session() as db:
                messages = self._chat_use_case(db).get_last_chat_messages_since(channel_name, since)

            if not messages:
                logger.debug("Нет сообщений для анализа")
                continue

            chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
            prompt = (f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                      f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}")
            try:
                result = self.generate_response_in_chat(prompt, channel_name)
                self.current_stream_summaries.append(result)
                self.last_chat_summary_time = datetime.utcnow()
                logger.info(f"Создан периодический анализ чата: {result}")
            except Exception as e:
                logger.error(f"Ошибка в summarize_chat_periodically: {e}")
            finally:
                db.close()

    async def check_minigames_periodically(self):
        logger.info("Запуск периодической проверки мини-игр")
        while True:
            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст в check_minigames_periodically. Пропускаем проверку мини-игр.")
                    await asyncio.sleep(60)
                    continue

                channel_name = self.initial_channels[0]

                rps_game_complete_time = self.minigame_service.check_rps_game_complete_time(channel_name, datetime.utcnow())

                if rps_game_complete_time:
                    game = self.minigame_service.get_active_rps_game(channel_name)
                    bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game)
                    if winners:
                        share = max(1, game.bank // len(winners))
                        with SessionLocal.begin() as db:
                            for winner in winners:
                                self._economy_service(db).add_balance(channel_name, winner, share, TransactionType.MINIGAME_WIN,
                                                                      f"Победа в КНБ ({winning_choice})")
                        winners_display = ", ".join(f"@{winner}" for winner in winners)
                        message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}."
                    else:
                        message = f"Выбор бота: {bot_choice}. Побеждает вариант: {winning_choice}. Победителей нет. Банк {game.bank} монет сгорает."
                    with SessionLocal.begin() as db:
                        self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), message, datetime.utcnow())
                    await self.get_channel(channel_name).send(message)
                    return

                expired_games = self.minigame_service.check_expired_games()
                for channel, timeout_message in expired_games.items():
                    await self.get_channel(channel).send(timeout_message)
                    with SessionLocal.begin() as db:
                        self._chat_use_case(db).save_chat_message(channel, self.nick.lower(), timeout_message, datetime.utcnow())

                with db_ro_session() as db:
                    active_stream = self.stream_service.get_active_stream(db, channel_name)

                if not active_stream:
                    await asyncio.sleep(60)
                    continue

                if channel_name not in self.minigame_service.stream_start_time:
                    self.minigame_service.set_stream_start_time(channel_name, active_stream.started_at)

                if not self.minigame_service.should_start_new_game(channel_name):
                    await asyncio.sleep(60)
                    continue

                broadcaster_id = await self._get_user_id_cached(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name} для мини-игр")
                    await asyncio.sleep(60)
                    continue

                choice = random.choice(["number", "word", "rps"])

                if choice == "word":
                    with db_ro_session() as db:
                        used_words = self.minigame_service.get_used_words(db, channel_name, limit=50)
                        last_messages = self._chat_use_case(db).get_last_chat_messages(channel_name, limit=50)

                    chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
                    if used_words:
                        avoid_clause = "\n\nНе используй ранее загаданные слова: " + ", ".join(sorted(set(used_words)))
                    else:
                        avoid_clause = ""

                    prompt = (
                        "Проанализируй последние сообщения из чата и выбери одно подходящее русское существительное (ОДНО слово),"
                        " связанное по смыслу с обсуждаемыми темами. Придумай короткую подсказку-описание к нему. Не повторяйся в загаданных словах." + avoid_clause +
                        "\nОтвет верни строго в JSON без дополнительного текста: {\"word\": \"слово\", \"hint\": \"краткая подсказка\"}."
                        "\nТребования: слово только из букв, без пробелов и дефисов; подсказка до 100 символов."
                        "\n\nВот сообщения чата (ник: текст):\n" + chat_text
                    )

                    system_prompt = self.SYSTEM_PROMPT_FOR_GROUP
                    ai_messages = [AIMessage(Role.SYSTEM, system_prompt), AIMessage(Role.USER, prompt)]

                    response = self._llm_client.generate_ai_response(ai_messages)

                    with SessionLocal.begin() as db:
                        self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, response)

                    data = json.loads(response)
                    word = str(data.get("word", "")).strip()
                    hint = str(data.get("hint", "")).strip()
                    final_word = word.strip().lower()

                    game = self.minigame_service.start_word_guess_game(channel_name, final_word, hint)
                    with SessionLocal.begin() as db:
                        self.minigame_service.add_used_word(db, channel_name, final_word)

                    masked = game.get_masked_word()
                    game_message = (
                        f"НОВАЯ ИГРА 'поле чудес'! Слово из {len(game.target_word)} букв. Подсказка: {hint}. "
                        f"Слово: {masked}. Приз: до {self.minigame_service.WORD_GAME_MAX_PRIZE} монет. "
                        f"Угадывайте буквы: {self._prefix}{self._COMMAND_GUESS_LETTER} <буква> или слово: {self._prefix}{self._COMMAND_GUESS_WORD} <слово>. "
                        f"Время на игру: {self.minigame_service.WORD_GAME_DURATION_MINUTES} минут"
                    )
                    logger.info(f"Запущена новая игра 'поле чудес' в канале {channel_name}")
                    messages = self.split_text(game_message)
                    for msg in messages:
                        await self.get_channel(channel_name).send(msg)
                        await asyncio.sleep(0.3)
                        with SessionLocal.begin() as db:
                            self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), game_message, datetime.utcnow())
                if choice == "number":
                    game = self.minigame_service.start_guess_number_game(channel_name)
                    game_message = (f"🎯 НОВАЯ МИНИ-ИГРА! Угадай число от {game.min_number} до {game.max_number}! "
                                    f"Первый, кто угадает, получит приз до {self.minigame_service.GUESS_GAME_PRIZE} монет! "
                                    f"Используй: {self._prefix}{self._COMMAND_GUESS} [число]. "
                                    f"Время на игру: {self.minigame_service.GUESS_GAME_DURATION_MINUTES} минут ⏰")
                    logger.info(f"Запущена новая игра 'угадай число' в канале {channel_name}")
                    messages = self.split_text(game_message)
                    for msg in messages:
                        await self.get_channel(channel_name).send(msg)
                        await asyncio.sleep(0.3)
                    with SessionLocal.begin() as db:
                        self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), game_message, datetime.utcnow())
                if choice == "rps":
                    self.minigame_service.start_rps_game(channel_name)
                    game_message = (
                        f"✊✌️🖐 НОВАЯ ИГРА КНБ! Банк старт: {self.minigame_service.RPS_BASE_BANK} монет + {self.minigame_service.RPS_ENTRY_FEE_PER_USER}"
                        f" за каждого участника. "
                        f"Участвовать: {self._prefix}{self._COMMAND_RPS} <камень/ножницы/бумага> — взнос {self.minigame_service.RPS_ENTRY_FEE_PER_USER} монет. "
                        f"Время на голосование: {self.minigame_service.RPS_GAME_DURATION_MINUTES} минуты ⏰"
                    )
                    logger.info(f"Запущена новая игра КНБ в канале {channel_name}")
                    messages = self.split_text(game_message)
                    for msg in messages:
                        await self.get_channel(channel_name).send(msg)
                        await asyncio.sleep(0.3)
                    with SessionLocal.begin() as db:
                        self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), game_message, datetime.utcnow())

            except Exception as e:
                logger.error(f"Ошибка в check_minigames_periodically: {e}")

            await asyncio.sleep(60)

    async def check_viewer_time_periodically(self):
        logger.info("Запуск периодической проверки времени просмотра")
        while True:
            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст в check_viewer_time_periodically")
                    await asyncio.sleep(self._CHECK_VIEWERS_INTERVAL_SECONDS)
                    continue

                channel_name = self.initial_channels[0]
                with db_ro_session() as db:
                    active_stream = self.stream_service.get_active_stream(db, channel_name)

                if not active_stream:
                    await asyncio.sleep(self._CHECK_VIEWERS_INTERVAL_SECONDS)
                    continue

                with SessionLocal.begin() as db:
                    self.viewer_service.check_inactive_viewers(db, active_stream.id, datetime.utcnow())

                broadcaster_id = await self._get_user_id_cached(channel_name)
                moderator_id = await self._get_user_id_cached(self.nick)
                chatters = await self.twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
                if chatters:
                    with SessionLocal.begin() as db:
                        self.viewer_service.update_viewers(db, active_stream.id, channel_name, chatters, datetime.utcnow())

                with db_ro_session() as db:
                    viewers_count = self.viewer_service.get_stream_watchers_count(db, active_stream.id)

                if viewers_count > active_stream.max_concurrent_viewers:
                    with SessionLocal.begin() as db:
                        self.stream_service.update_max_concurrent_viewers_count(db, active_stream.id, viewers_count)

                with SessionLocal.begin() as db:
                    viewer_sessions = self.viewer_service.get_stream_viewer_sessions(db, active_stream.id)
                    for session in viewer_sessions:
                        available_rewards = self.viewer_service.get_available_rewards(session)
                        for minutes_threshold, reward_amount in available_rewards:
                            claimed_list = session.get_claimed_rewards_list()
                            claimed_list.append(minutes_threshold)
                            rewards = ','.join(map(str, sorted(claimed_list)))
                            self.viewer_service.update_session_rewards(db, session.id, rewards, datetime.utcnow())
                            self._economy_service(db).add_balance(channel_name, session.user_name, reward_amount,
                                                                  TransactionType.VIEWER_TIME_REWARD, description)
                            description = f"Награда за {minutes_threshold} минут просмотра стрима"

            except Exception as e:
                logger.error(f"Ошибка в check_viewer_time_periodically: {e}")

            await asyncio.sleep(self._CHECK_VIEWERS_INTERVAL_SECONDS)

    def _restore_stream_context(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст при восстановлении контекста стрима")
                return

            channel_name = self.initial_channels[0]
            with db_ro_session() as db:
                active_stream = self.stream_service.get_active_stream(db, channel_name)

            if active_stream:
                self.minigame_service.set_stream_start_time(channel_name, active_stream.started_at)
                logger.info(f"Найден активный стрим ID {active_stream.id}")
            else:
                logger.info("Активных стримов не найдено")
        except Exception as e:
            logger.error(f"Ошибка при восстановлении состояния стрима: {e}")

    def generate_response_in_chat(self, prompt: str, channel_name: str) -> str:
        messages = []
        with db_ro_session() as db:
            last_messages = self._ai_conversation_use_case(db).get_last_messages(channel_name, self.SYSTEM_PROMPT_FOR_GROUP)
        messages.extend(last_messages)
        messages.append(AIMessage(Role.USER, prompt))
        assistant_message = self._llm_client.generate_ai_response(messages)
        return assistant_message
