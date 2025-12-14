import asyncio
import logging
import random
import json
from typing import Coroutine, Any
from telegram.request import HTTPXRequest
from twitchio.ext import commands
from datetime import datetime, timedelta
import telegram
from config import config
from db.base import SessionLocal
from features.ai.ai_service import AIService
from features.ai.intent import Intent
from features.ai.message import AIMessage, Role
from features.betting.betting_service import BettingService
from features.equipment.equipment_service import EquipmentService
from features.twitch.api.twitch_api_service import TwitchApiService
from features.twitch.auth import TwitchAuth
from features.stream.db.stream_messages import ChatMessageLog
from features.economy.db.transaction_history import TransactionType
from features.twitch.twitch_repository import TwitchService
from features.settings.settings_manager import SettingsManager
from features.economy.economy_service import EconomyService
from features.minigame.minigame_service import MinigameService
from features.stream.stream_service import StreamService
from features.stream.viewer_time_service import ViewerTimeService
from features.stream.model.stream_statistics import StreamStatistics
from features.betting.model.rarity_level import RarityLevel
from features.betting.model.emoji_config import EmojiConfig
from features.economy.model.shop_items import ShopItems

logger = logging.getLogger(__name__)


class Bot(commands.Bot):
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

    def __init__(self, twitch_auth: TwitchAuth, twitch_api_service: TwitchApiService, twitch_repository: TwitchService, ai_repository: AIService):
        self._prefix = '!'
        self.initial_channels = ['artemnefrit']
        super().__init__(token=twitch_auth.access_token, prefix=self._prefix, initial_channels=self.initial_channels)

        self.twitch_auth = twitch_auth
        self.twitch_api_service = twitch_api_service
        self.twitch_repository = twitch_repository
        self.ai_repository = ai_repository
        self.settings_manager = SettingsManager()
        self.stream_service = StreamService()
        self.equipment_service = EquipmentService()
        self.economy_service = EconomyService(self.stream_service)
        self.minigame_service = MinigameService(self.economy_service)
        self.viewer_service = ViewerTimeService(self.economy_service)
        self.betting_service = BettingService(self.economy_service)

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

        logger.debug(f"Получено сообщение от {nickname} в канале {channel_name}: {content}")

        self.twitch_repository.log_chat_message(channel_name, nickname, content)

        try:
            reward_result = self.economy_service.process_user_message_activity(channel_name, nickname)
            if reward_result:
                logger.info(f"Награда за активность: {nickname} получил {self.economy_service.ACTIVITY_REWARD} монет")
        except Exception as e:
            logger.error(f"Ошибка при обработке активности пользователя {nickname}: {e}")

        try:
            active_stream = self.stream_service.get_active_stream(channel_name)
            if active_stream:
                self.viewer_service.update_activity(active_stream.id, channel_name, nickname)
        except Exception as e:
            logger.error(f"Ошибка при обновлении времени просмотра для {nickname}: {e}")

        if message.content.startswith(self._prefix):
            logger.debug(f"Обработка команды: {message.content}")
            await self.handle_commands(message)
            return

        intent = self.ai_repository.extract_intent_from_text(message.content)
        logger.debug(f"Определён интент: {intent}")

        prompt = None

        if intent == Intent.JACKBOX:
            prompt = self.ai_repository.get_jackbox_prompt(self._SOURCE_TWITCH, nickname, content)
        elif intent == Intent.DANKAR_CUT:
            prompt = self.ai_repository.get_dankar_cut_prompt(self._SOURCE_TWITCH, nickname, content)
        elif intent == Intent.HELLO:
            prompt = self.ai_repository.get_hello_prompt(self._SOURCE_TWITCH, nickname, content)

        if prompt is not None:
            result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
            await self._post_message_in_twitch_chat(result, message.channel)
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
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
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
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
            result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
            self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
        else:
            result = f'@{user_name}, вы не отслеживаете канал {channel_name}.'
            logger.info(f"Пользователь {user_name} не подписан на канал {channel_name}")
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)

    @commands.command(name=_COMMAND_GLADDI)
    async def ask(self, ctx):
        channel_name = ctx.channel.name
        full_message = ctx.message.content
        question = full_message[len(f"{self._prefix}{self._COMMAND_GLADDI}"):].strip()
        nickname = ctx.author.display_name

        logger.info(f"Команда от пользователя {nickname}")

        intent = self.ai_repository.extract_intent_from_text(question)
        logger.info(f"Определён интент: {intent}")

        if intent == Intent.JACKBOX:
            prompt = self.ai_repository.get_jackbox_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self.ai_repository.get_skuf_femboy_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.DANKAR_CUT:
            prompt = self.ai_repository.get_dankar_cut_prompt(self._SOURCE_TWITCH, nickname, question)
        elif intent == Intent.HELLO:
            prompt = self.ai_repository.get_hello_prompt(self._SOURCE_TWITCH, nickname, question)
        else:
            prompt = self.ai_repository.get_default_prompt(self._SOURCE_TWITCH, nickname, question)

        result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
        self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)
        self.twitch_repository.log_chat_message(channel_name, self.nick, result)
        logger.info(f"Отправлен ответ пользователю {nickname}")
        await self._post_message_in_twitch_chat(result, ctx)

    @commands.command(name=_COMMAND_FIGHT)
    async def battle(self, ctx):
        channel_name = ctx.channel.name
        challenger = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_FIGHT} от пользователя {challenger}")

        if not self.economy_service.can_join_battle(channel_name, challenger):
            result = f"@{challenger}, недостаточно монет для участия в битве! Необходимо: {self.economy_service.BATTLE_ENTRY_FEE} монет. 💰"
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        if not self.battle_waiting_user:
            user_balance = self.economy_service.process_battle_entry(channel_name, challenger)
            if not user_balance:
                result = f"@{challenger}, произошла ошибка при списании взноса за битву."
                self.twitch_repository.log_chat_message(channel_name, self.nick, result)
                await ctx.send(result)
                return

            self.battle_waiting_user = challenger
            result = f"⚔️ @{challenger} ищет себе оппонента для эпичной битвы! Взнос: {self.economy_service.BATTLE_ENTRY_FEE} монет. Используй {self._prefix}{self._COMMAND_FIGHT}, чтобы принять вызов. Баланс {challenger}: {user_balance.balance} монет."
            logger.info(f"{challenger} ищет оппонента для битвы")
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        if self.battle_waiting_user == challenger:
            result = f"@{challenger}, ты не можешь сражаться сам с собой. Подожди достойного противника."
            logger.warning(f"{challenger} пытается сражаться сам с собой")
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        challenger_balance = self.economy_service.process_battle_entry(channel_name, challenger)
        if not challenger_balance:
            result = f"@{challenger}, произошла ошибка при списании взноса за битву."
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        opponent = self.battle_waiting_user
        self.battle_waiting_user = None

        logger.info(f"Начинается битва между {opponent} и {challenger}")

        opponent_equipment = self.equipment_service.get_user_equipment(channel_name, opponent)
        challenger_equipment = self.equipment_service.get_user_equipment(channel_name, challenger)

        prompt = (
            f"На арене сражаются два героя: {opponent} и {challenger}."
            "\nСимулируй юмористическую и эпичную битву между ними, с абсурдом и неожиданными поворотами."
        )

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
            f"\n\nПроигравший получит таймаут! Победитель получит {self.economy_service.BATTLE_WINNER_PRIZE} монет!"
        )

        result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)

        logger.info(f"Битва завершена. Случайно выбранный победитель: {winner}")

        winner_balance = self.economy_service.process_battle_win(channel_name, winner, loser)

        self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)
        self.twitch_repository.log_chat_message(channel_name, self.nick, result)
        self.twitch_repository.save_battle_history(channel_name, opponent, challenger, winner, result)

        messages = self.split_text(result)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        logger.info(f"Проигравший: {loser}, получает таймаут")

        winner_message = f"💰 {winner} получает {self.economy_service.BATTLE_WINNER_PRIZE} монет! Баланс: {winner_balance.balance} монет."
        await ctx.send(winner_message)

        self.twitch_repository.log_chat_message(channel_name, self.nick, winner_message)
        await asyncio.sleep(1)

        base_battle_timeout = 120

        equipment = self.equipment_service.get_user_equipment(channel_name, loser)
        final_timeout, protection_message = self.economy_service.calculate_timeout_with_equipment(loser, base_battle_timeout, equipment)

        if final_timeout == 0:
            no_timeout_message = f"⚔️ @{loser}, спасен от таймаута! {protection_message}"
            await ctx.send(no_timeout_message)
            self.twitch_repository.log_chat_message(channel_name, self.nick, no_timeout_message)
        else:
            timeout_minutes = final_timeout // 60
            timeout_seconds_remainder = final_timeout % 60

            if timeout_minutes > 0:
                time_display = f"{timeout_minutes} минут" if timeout_seconds_remainder == 0 else f"{timeout_minutes}м {timeout_seconds_remainder}с"
            else:
                time_display = f"{timeout_seconds_remainder} секунд"

            reason = f"Поражение в битве! Время на тренировки: {time_display} ⚔️"

            if protection_message:
                reason += f" {protection_message}"

            await self._timeout_user(ctx, loser, final_timeout, reason)

    @commands.command(name=_COMMAND_ROLL)
    async def roll(self, ctx, amount: str = None):
        channel_name = ctx.channel.name
        nickname = ctx.author.display_name

        bet_amount = self.betting_service.BET_COST
        if amount:
            try:
                bet_amount = int(amount)
            except ValueError:
                result = (f"@{nickname}, неверная сумма ставки! Используй: {self._prefix}{self._COMMAND_ROLL} [сумма] (например: {self._prefix}{self._COMMAND_ROLL} 100). "
                          f"Диапазон: {self.betting_service.MIN_BET_AMOUNT}-{self.betting_service.MAX_BET_AMOUNT} монет.")
                self.twitch_repository.log_chat_message(channel_name, self.nick, result)
                await ctx.send(result)
                return

        logger.info(f"Команда {self._COMMAND_ROLL} от пользователя {nickname}, сумма ставки: {bet_amount}")

        current_time = datetime.now()
        equipment = self.equipment_service.get_user_equipment(channel_name, nickname)
        cooldown_seconds = self.economy_service.calculate_roll_cooldown_seconds(self._ROLL_COOLDOWN_SECONDS, equipment)

        if nickname in self.roll_cooldowns:
            time_since_last = (current_time - self.roll_cooldowns[nickname]).total_seconds()
            if time_since_last < cooldown_seconds:
                remaining_time = cooldown_seconds - time_since_last
                result = f"@{nickname}, подожди ещё {remaining_time:.0f} секунд перед следующей ставкой! ⏰"
                logger.info(f"Пользователь {nickname} попытался использовать команду в кулдауне. Осталось: {remaining_time:.0f} сек")
                self.twitch_repository.log_chat_message(channel_name, self.nick, result)
                await ctx.send(result)
                return

        self.roll_cooldowns[nickname] = current_time
        logger.debug(f"Обновлен кулдаун для пользователя {nickname}: {current_time}")

        emojis = EmojiConfig.get_emojis_list()
        weights = EmojiConfig.get_weights_list()

        slot_results = random.choices(emojis, weights=weights, k=3)
        slot_result_string = EmojiConfig.format_slot_result(slot_results)

        logger.info(f"Результат слот-машины для {nickname}: {slot_result_string}")

        has_dino_dance = 'DinoDance' in slot_results
        dino_dance_count = slot_results.count('DinoDance')

        if has_dino_dance:
            logger.warning(f"🦕 МИФИЧЕСКИЙ СМАЙЛИК! DinoDance выпал {dino_dance_count} раз(а) у {nickname}!")
            logger.info(f"СТАТИСТИКА DINO: пользователь={nickname}, канал={channel_name}, результат={slot_result_string}, время={datetime.now()}")

        unique_results = set(slot_results)

        if len(unique_results) == 1:
            db_result_type = "jackpot"
        elif len(unique_results) == 2:
            db_result_type = "partial"
        else:
            db_result_type = "miss"

        equipment = self.equipment_service.get_user_equipment(channel_name, nickname)
        bet_result = self.betting_service.process_bet_result_with_amount(channel_name, nickname, db_result_type, slot_result_string, bet_amount, equipment)

        if not bet_result.success:
            result = bet_result.message
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        try:
            rarity_enum = RarityLevel(bet_result.rarity)
            self.twitch_repository.save_bet_history(channel_name=channel_name, user_name=nickname, slot_result=slot_result_string, result_type=db_result_type,
                                                    rarity_level=rarity_enum)
            logger.info(f"Результат ставки сохранён в БД для {nickname}: {slot_result_string}, редкость: {bet_result.rarity}")
        except Exception as e:
            logger.error(f"Ошибка сохранения результата ставки в БД: {e}")

        economic_info = f" {bet_result.get_result_emoji()} Баланс: {bet_result.balance} монет"
        profit_display = bet_result.get_profit_display()
        if profit_display:
            economic_info += f" ({profit_display})"

        final_result = f"{slot_result_string} {economic_info}"

        self.twitch_repository.log_chat_message(channel_name, self.nick, final_result)

        messages = self.split_text(final_result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

        if bet_result.should_timeout():
            base_timeout_duration = bet_result.get_timeout_duration()

            equipment = self.equipment_service.get_user_equipment(channel_name, nickname)
            final_timeout, protection_message = self.economy_service.calculate_timeout_with_equipment(nickname, base_timeout_duration, equipment)

            if final_timeout == 0:
                if bet_result.is_consolation_prize():
                    no_timeout_message = f"🎁 @{nickname}, спасен от таймаута! {protection_message} Консольный приз: {bet_result.payout} монет"
                else:
                    no_timeout_message = f"🛡️ @{nickname}, спасен от таймаута! {protection_message}"

                self.twitch_repository.log_chat_message(channel_name, self.nick, no_timeout_message)

                messages = self.split_text(no_timeout_message)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)
            else:
                if bet_result.is_consolation_prize():
                    reason = f"Промах с редким эмодзи! Консольный приз: {bet_result.payout} монет. Таймаут: {final_timeout} сек ⏰"
                else:
                    reason = f"Промах в слот-машине! Время на размышления: {final_timeout} сек ⏰"

                if protection_message:
                    reason += f" {protection_message}"

                messages = self.split_text(reason)
                for msg in messages:
                    await ctx.send(msg)
                    await asyncio.sleep(0.3)

                await self._timeout_user(ctx, nickname, final_timeout, reason)
        elif bet_result.is_miss():
            if bet_result.is_consolation_prize():
                no_timeout_message = f"🎁 @{nickname}, повезло! Редкий эмодзи спас от таймаута! Консольный приз: {bet_result.payout} монет"
            else:
                no_timeout_message = f"✨ @{nickname}, редкий эмодзи спас от таймаута!"

            messages = self.split_text(no_timeout_message)
            for msg in messages:
                await ctx.send(msg)
                await asyncio.sleep(0.3)
            self.twitch_repository.log_chat_message(channel_name, self.nick, no_timeout_message)

        self._cleanup_old_cooldowns()

    @commands.command(name=_COMMAND_BALANCE)
    async def balance(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_BALANCE} от пользователя {user_name}")

        user_balance = self.economy_service.get_user_balance(channel_name, user_name)
        result = f"💰 @{user_name}, твой баланс: {user_balance.balance} монет"

        if self.economy_service.can_claim_daily_bonus(channel_name, user_name):
            result += f" | Доступен бонус! Используй {self._prefix}{self._COMMAND_BONUS}"

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)
        await ctx.send(result)

    @commands.command(name=_COMMAND_BONUS)
    async def daily_bonus(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_BONUS} от пользователя {user_name}")

        user_equipment = self.equipment_service.get_user_equipment(channel_name, user_name)
        bonus_result = self.economy_service.claim_daily_bonus(channel_name, user_name, user_equipment)

        if bonus_result.success:
            if bonus_result.bonus_message:
                result = f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! Баланс: {bonus_result.user_balance.balance} монет. {bonus_result.bonus_message}"
            else:
                result = f"🎁 @{user_name} получил бонус {bonus_result.bonus_amount} монет! Баланс: {bonus_result.user_balance.balance} монет"
        else:
            if bonus_result.failure_reason == "no_stream":
                result = f"🚫 @{user_name}, бонус доступен только во время стрима!"
            elif bonus_result.failure_reason == "already_claimed":
                result = f"⏰ @{user_name}, бонус уже получен на этом стриме!"
            elif bonus_result.failure_reason == "error":
                result = f"❌ @{user_name}, произошла ошибка при получении бонуса. Попробуй позже!"
            else:
                result = f"❌ @{user_name}, бонус недоступен!"

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

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
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        try:
            transfer_amount = int(amount)
        except ValueError:
            result = f"@{sender_name}, неверная сумма! Укажи число. Например: {self._prefix}{self._COMMAND_TRANSFER} {recipient} 100"
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        if transfer_amount <= 0:
            result = f"@{sender_name}, сумма должна быть больше 0!"
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        recipient = recipient.lstrip('@')

        transfer_result = self.economy_service.transfer_money(channel_name, sender_name, recipient, transfer_amount)

        if transfer_result.success:
            result = transfer_result.get_success_message()
        else:
            result = transfer_result.get_error_message(sender_name)

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)
        await ctx.send(result)

    @commands.command(name=_COMMAND_SHOP)
    async def shop(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_SHOP} от пользователя {user_name}")

        all_items = ShopItems.get_all_items()

        result = "🛒 МАГАЗИН АРТЕФАКТОВ:\n"

        sorted_items = sorted(all_items.items(), key=lambda x: x[1].price)

        for item_type, item in sorted_items:
            result += f"{item.emoji} {item.name} - {item.price} монет. "

        result += f"Используй: {self._prefix}{self._COMMAND_BUY} [название предмета]. Пример: {self._prefix}{self._COMMAND_BUY} стул. Все предметы действуют 30 дней!"

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

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
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        purchase_result = self.economy_service.purchase_item(channel_name, user_name, item_name.strip())

        if purchase_result["success"]:
            item = purchase_result["item"]
            expires_date = purchase_result["expires_at"].strftime("%d.%m.%Y")
            result = f"🎉 @{user_name} купил {item.emoji} '{item.name}' за {item.price} монет! "
            result += f"Действует до {expires_date}. Баланс: {purchase_result['new_balance']} монет."
        else:
            result = f"❌ @{user_name}, {purchase_result['message']}"

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)
        await ctx.send(result)

    @commands.command(name=_COMMAND_EQUIPMENT)
    async def equipment(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_EQUIPMENT} от пользователя {user_name}")

        equipment = self.equipment_service.get_user_equipment(channel_name, user_name)

        if not equipment:
            result = f"📦 @{user_name}, у вас нет активной экипировки. Загляните в {self._prefix}{self._COMMAND_SHOP}!"
        else:
            result = f"⚔️ Экипировка @{user_name}:\n"

            for item in equipment:
                expires_date = item.expires_at.strftime("%d.%m.%Y")
                result += f"{item.shop_item.emoji} {item.shop_item.name} до {expires_date}\n"

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_TOP)
    async def top_users(self, ctx):
        channel_name = ctx.channel.name

        logger.info(f"Команда {self._COMMAND_TOP}")

        top_users = self.economy_service.get_top_users(channel_name, limit=5)

        if not top_users:
            result = "Нет данных для отображения топа."
        else:
            result = "👑 ТОП БОГАЧЕЙ:\n"
            for i, user in enumerate(top_users, 1):
                medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
                result += f"{medal} {user['user_name']}: {user['balance']} монет. "

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

        messages = self.split_text(result)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_BOTTOM)
    async def bottom_users(self, ctx):
        channel_name = ctx.channel.name

        logger.info(f"Команда {self._COMMAND_BOTTOM}")

        bottom_users = self.economy_service.get_bottom_users(channel_name, limit=10)

        if not bottom_users:
            result = "Нет данных для отображения бомжей."
        else:
            result = "💸 ТОП БОМЖЕЙ:\n"
            for i, user in enumerate(bottom_users, 1):
                emoji = "🗑️" if i == 1 else "📦" if i == 2 else "🥫" if i == 3 else f"{i}."
                result += f"{emoji} {user['user_name']}: {user['balance']} монет. "

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

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

        self.twitch_repository.log_chat_message(channel_name, self.nick, help_text)

        messages = self.split_text(help_text)
        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    @commands.command(name=_COMMAND_STATS)
    async def user_stats(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name

        logger.info(f"Команда {self._COMMAND_STATS} от пользователя {user_name}")

        stats = self.economy_service.get_user_stats(channel_name, user_name)
        bet_stats = self.twitch_repository.get_user_bet_stats(user_name, channel_name)
        battle_stats = self.twitch_repository.get_user_battle_stats(user_name, channel_name)

        result = f"📊 Статистика @{user_name}: "
        result += f"💰 Баланс: {stats.balance} монет."
        result += f"📈 Всего заработано: {stats.total_earned} монет. "
        result += f"📉 Всего потрачено: {stats.total_spent} монет. "
        result += f"💹 Чистая прибыль: {stats.net_profit} монет. "

        if bet_stats['total_bets'] > 0:
            result += f"\n🎰 Ставки: {bet_stats['total_bets']} | "
            result += f"Джекпоты: {bet_stats['jackpots']} ({bet_stats['jackpot_rate']:.1f}%). "
            if bet_stats['mythical_count'] > 0:
                result += f"🦕 Мифических: {bet_stats['mythical_count']} ({bet_stats['mythical_rate']:.3f}%). "

        if battle_stats.has_battles():
            result += f"⚔️ Битвы: {battle_stats.total_battles} | "
            result += f"Побед: {battle_stats.wins} ({battle_stats.win_rate:.1f}%). "

        if stats.is_profitable():
            result += f"📈 Поздравляю, ты в прибыли! "
        elif stats.net_profit < 0:
            result += f"📉 Ты в убытке artemn3Cry "

        self.twitch_repository.log_chat_message(channel_name, self.nick, result)

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
            game_status = self.minigame_service.get_game_status(channel_name)
            if game_status:
                result = game_status
            else:
                result = f"@{user_name}, сейчас нет активной игры 'угадай число'. Используй: {self._prefix}{self._COMMAND_GUESS} [число]"

            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        try:
            guess = int(number)
        except ValueError:
            result = f"@{user_name}, укажи правильное число! Например: {self._prefix}{self._COMMAND_GUESS} 42"
            self.twitch_repository.log_chat_message(channel_name, self.nick, result)
            await ctx.send(result)
            return

        success, message = self.minigame_service.process_guess(channel_name, user_name, guess)

        self.twitch_repository.log_chat_message(channel_name, self.nick, message)
        await ctx.send(message)

    @commands.command(name=_COMMAND_GUESS_LETTER)
    async def guess_letter(self, ctx, letter: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not letter:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                self.twitch_repository.log_chat_message(channel_name, self.nick, status)
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return
        success, message = self.minigame_service.process_letter(channel_name, user_name, letter)
        await ctx.send(message)
        self.twitch_repository.log_chat_message(channel_name, self.nick, message)

    @commands.command(name=_COMMAND_GUESS_WORD)
    async def guess_word(self, ctx, *, word: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not word:
            status = self.minigame_service.get_word_game_status(channel_name)
            if status:
                await ctx.send(status)
                self.twitch_repository.log_chat_message(channel_name, self.nick, status)
            else:
                await ctx.send(f"@{user_name}, сейчас нет активной игры 'поле чудес' — дождитесь автоматического запуска.")
            return
        success, message = self.minigame_service.process_word(channel_name, user_name, word)
        await ctx.send(message)
        self.twitch_repository.log_chat_message(channel_name, self.nick, message)

    @commands.command(name=_COMMAND_RPS)
    async def join_rps(self, ctx, choice: str = None):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        if not choice:
            await ctx.send(f"@{user_name}, укажите ваш выбор: камень / ножницы / бумага")
            return
        success, message = self.minigame_service.join_rps(channel_name, user_name, choice)
        await ctx.send(message)
        self.twitch_repository.log_chat_message(channel_name, self.nick, message)

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
        logger.debug(f"Отправка сообщения в чат: {message}")
        messages = self.split_text(message)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def post_joke_periodically(self):
        logger.info("Запуск периодической генерации анекдотов")
        while True:
            await asyncio.sleep(30)

            if not self.settings_manager.should_generate_jokes():
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
                result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
                self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)
                self.twitch_repository.log_chat_message(channel_name, self.nick, result)
                channel = self.get_channel(channel_name)
                await channel.send(result)
                logger.info(f"Анекдот сгенерирован: {result}")

                success = self.settings_manager.mark_joke_generated()
                if success:
                    next_joke_info = self.settings_manager.get_next_joke_info()
                    logger.info(f"Следующий анекдот запланирован на: {next_joke_info.get('next_joke_time')}")

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

                active_stream = self.stream_service.get_active_stream(channel_name)

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
                        self.stream_service.create_stream(channel_name, started_at, game_name, title)
                        self.minigame_service.set_stream_start_time(channel_name, started_at)
                        await self.stream_announcement(game_name, title, channel_name)
                        self.current_stream_summaries = []
                    except Exception as e:
                        logger.error(f"Ошибка при создании стрима: {e}")

                elif not stream_status.is_online and active_stream is not None:
                    logger.info("Стрим завершён")
                    finish_time = datetime.utcnow()
                    self.stream_service.end_stream(active_stream.id, finish_time)
                    self.viewer_service.finish_stream_sessions(active_stream.id)
                    total_viewers = self.viewer_service.get_unique_viewers_count(active_stream.id)
                    self.stream_service.update_stream_total_viewers(active_stream.id, total_viewers)
                    self.minigame_service.reset_stream_state(channel_name)
                    logger.info(f"Стрим завершен в БД: ID {active_stream.id}")

                    stats = self.twitch_repository.get_stream_statistics(channel_name, active_stream.started_at)

                    try:
                        await self.stream_summarize(stats, channel_name, active_stream.started_at, finish_time)
                    except Exception as e:
                        logger.error(f"Ошибка при вызове stream_summarize: {e}")

                elif stream_status.is_online and active_stream:
                    if active_stream.game_name != game_name or active_stream.title != title:
                        self.stream_service.update_stream_metadata(active_stream.id, game_name, title)
                        logger.info(f"Обновлены метаданные стрима: игра='{game_name}', название='{title}'")

            except Exception as e:
                logger.error(f"Ошибка в check_stream_start_periodically: {e}")

            await asyncio.sleep(60)

    async def stream_announcement(self, game_name: str, title: str, channel_name: str):
        prompt = f"Начался стрим. Категория: {game_name}, название: {title}. Сгенерируй краткий анонс для телеграм канала. Ссылка на трансляцию: https://twitch.tv/artemnefrit"
        result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
        try:
            await self.telegram_bot.send_message(chat_id=self._GROUP_ID, text=result)
            self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)
            logger.info(f"Анонс стрима отправлен в Telegram: {result}")
        except Exception as e:
            logger.error(f"Ошибка отправки анонса в Telegram: {e}")

    async def stream_summarize(self, stream_stat: StreamStatistics, channel_name: str, stream_start_dt, stream_end_dt):
        logger.info("Создание итогового отчёта о стриме")

        if self.last_chat_summary_time is None:
            self.last_chat_summary_time = stream_start_dt

        last_messages = self.twitch_repository.get_chat_messages(channel_name, self.last_chat_summary_time, stream_end_dt)

        if last_messages:
            chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)
            prompt = (
                f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}"
            )
            result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
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
            user_balance = self.economy_service.add_balance(channel_name, top_user, reward_amount, TransactionType.SPECIAL_EVENT,
                                                            "Награда за самую высокую активность в стриме")
            stream_stat_message += f"{top_user} получает награду {reward_amount} монет за активность! Баланс: {user_balance.balance} монет."

        logger.info(f"Статистика стрима: {stream_stat_message}")

        prompt = f"Трансляция была завершена. Статистика:\n{stream_stat_message}"

        if self.current_stream_summaries:
            summary_text = "\n".join(self.current_stream_summaries)
            prompt += f"\n\nВыжимки из того, что происходило в чате: {summary_text}"

        prompt += f"\n\nНа основе предоставленной информации подведи краткий итог трансляции"
        result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)

        self.twitch_repository.save_conversation_to_db(channel_name, prompt, result)

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

                active_stream = self.stream_service.get_active_stream(channel_name)
                if not active_stream:
                    logger.debug("Стрим не активен, пропускаем анализ чата")
                    continue
            except Exception as e:
                logger.error(f"Ошибка при проверке статуса стрима в summarize_chat_periodically: {e}")
                continue

            db = SessionLocal()
            try:
                since = datetime.utcnow() - timedelta(minutes=20)
                messages = (
                    db.query(ChatMessageLog)
                    .filter(ChatMessageLog.channel_name == channel_name)
                    .filter(ChatMessageLog.created_at >= since)
                    .order_by(ChatMessageLog.created_at.asc())
                    .all()
                )
                if not messages:
                    logger.debug("Нет сообщений для анализа")
                    continue
                chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)
                prompt = (f"Основываясь на сообщения в чате, подведи краткий итог общения. 1-5 тезисов. "
                          f"Напиши только сами тезисы, больше ничего. Без нумерации. Вот сообщения: {chat_text}")
                result = self.twitch_repository.generate_response_in_chat(prompt, channel_name)
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

                expired_games = self.minigame_service.check_expired_games()
                for channel, timeout_message in expired_games.items():
                    await self.get_channel(channel).send(timeout_message)
                    self.twitch_repository.log_chat_message(channel, self.nick, timeout_message)

                active_stream = self.stream_service.get_active_stream(channel_name)
                if not active_stream:
                    await asyncio.sleep(60)
                    continue

                if channel_name not in self.minigame_service.stream_start_time:
                    self.minigame_service.set_stream_start_time(channel_name, active_stream.started_at)

                if self.minigame_service.should_start_new_game(channel_name):
                    broadcaster_id = await self._get_user_id_cached(channel_name)

                    if not broadcaster_id:
                        logger.error(f"Не удалось получить ID канала {channel_name} для мини-игр")
                        continue

                    choice = random.choice(["number", "word", "rps"])

                    if choice == "word":
                        used_words = self.twitch_repository.get_used_words(channel_name, limit=50)
                        last_messages = self.twitch_repository.get_last_chat_messages(channel_name, limit=50)

                        if used_words:
                            avoid_clause = "\n\nНе используй ранее загаданные слова: " + ", ".join(sorted(set(used_words)))
                        else:
                            avoid_clause = ""

                        chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in last_messages)

                        prompt = (
                            "Проанализируй последние сообщения из чата и выбери одно подходящее русское существительное (ОДНО слово),"
                            " связанное по смыслу с обсуждаемыми темами. Придумай короткую подсказку-описание к нему. Не повторяйся в загаданных словах." + avoid_clause +
                            "\nОтвет верни строго в JSON без дополнительного текста: {\"word\": \"слово\", \"hint\": \"краткая подсказка\"}."
                            "\nТребования: слово только из букв, без пробелов и дефисов; подсказка до 100 символов."
                            "\n\nВот сообщения чата (ник: текст):\n" + chat_text
                        )

                        system_prompt = TwitchService.SYSTEM_PROMPT_FOR_GROUP
                        ai_messages = [AIMessage(Role.SYSTEM, system_prompt), AIMessage(Role.USER, prompt)]
                        response = self.ai_repository.generate_ai_response(ai_messages)

                        self.twitch_repository.save_conversation_to_db(channel_name, prompt, response)

                        data = json.loads(response)
                        word = str(data.get("word", "")).strip()
                        hint = str(data.get("hint", "")).strip()
                        final_word = word.lower()

                        game = self.minigame_service.start_word_guess_game(channel_name, final_word, hint)
                        self.twitch_repository.add_used_word(channel_name, final_word)

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
                        self.twitch_repository.log_chat_message(channel_name, self.nick, game_message)
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
                        self.twitch_repository.log_chat_message(channel_name, self.nick, game_message)
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
                        self.twitch_repository.log_chat_message(channel_name, self.nick, game_message)

            except Exception as e:
                logger.error(f"Ошибка в check_minigames_periodically: {e}")

            await asyncio.sleep(60)

    async def check_viewer_time_periodically(self):
        logger.info("Запуск периодической проверки времени просмотра")
        while True:
            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст в check_viewer_time_periodically")
                    await asyncio.sleep(self.viewer_service.CHECK_INTERVAL_SECONDS)
                    continue

                channel_name = self.initial_channels[0]
                active_stream = self.stream_service.get_active_stream(channel_name)

                if not active_stream:
                    await asyncio.sleep(self.viewer_service.CHECK_INTERVAL_SECONDS)
                    continue

                self.viewer_service.check_inactive_viewers(active_stream.id)

                broadcaster_id = await self._get_user_id_cached(channel_name)
                moderator_id = await self._get_user_id_cached(self.nick)
                chatters = await self.twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
                if chatters:
                    await self.viewer_service.update_viewers(active_stream.id, channel_name, chatters)
                viewers_count = self.viewer_service.get_stream_watchers_count(active_stream.id)
                if viewers_count > active_stream.max_concurrent_viewers:
                    self.stream_service.update_max_concurrent_viewers_count(active_stream.id, viewers_count)
                self.viewer_service.check_and_grant_rewards(active_stream.id, channel_name)
            except Exception as e:
                logger.error(f"Ошибка в check_viewer_time_periodically: {e}")

            await asyncio.sleep(self.viewer_service.CHECK_INTERVAL_SECONDS)

    def _restore_stream_context(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст при восстановлении контекста стрима")
                return

            channel_name = self.initial_channels[0]
            active_stream = self.stream_service.get_active_stream(channel_name)

            if active_stream:
                self.minigame_service.set_stream_start_time(channel_name, active_stream.started_at)
                logger.info(f"Восстановлено состояние: найден активный стрим ID {active_stream.id}")
            else:
                logger.info("Восстановлено состояние: активных стримов не найдено")
        except Exception as e:
            logger.error(f"Ошибка при восстановлении состояния стрима: {e}")
