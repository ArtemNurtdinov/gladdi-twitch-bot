import asyncio
import logging
from twitchio.ext import commands
from datetime import datetime, timedelta

from app.ai.domain.models import Intent, AIMessage, Role
from app.battle.domain.models import UserBattleStats
from app.betting.presentation.betting_schemas import UserBetStats
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.minigame.domain.minigame_service import MinigameService
from app.minigame.domain.models import RPS_CHOICES
from app.stream.domain.models import StreamStatistics
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.presentation.commands.ask import AskCommandHandler
from app.twitch.presentation.commands.battle import BattleCommandHandler
from app.twitch.presentation.commands.balance import BalanceCommandHandler
from app.twitch.presentation.commands.bonus import BonusCommandHandler
from app.twitch.presentation.commands.followage import FollowageCommandHandler
from app.twitch.presentation.commands.roll import RollCommandHandler
from app.twitch.presentation.commands.shop import ShopCommandHandler
from app.twitch.presentation.commands.transfer import TransferCommandHandler
from core.config import config
from collections import Counter

from core.db import db_ro_session, SessionLocal
from app.economy.domain.models import TransactionType

logger = logging.getLogger(__name__)


# noinspection PyDeprecation
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
    _CHECK_VIEWERS_INTERVAL_SECONDS = 10
    _CHECK_STREAM_STATUS_INTERVAL_SECONDS = 60

    def __init__(self, deps: BotDependencies):
        self._deps = deps
        self._prefix = '!'
        self.initial_channels = ['artemnefrit']
        super().__init__(token=deps.twitch_auth.access_token, prefix=self._prefix, initial_channels=self.initial_channels)

        self._llm_client = deps.llm_client
        self._intent_detector = deps.intent_detector
        self._intent_use_case = deps.intent_use_case
        self._prompt_service = deps.prompt_service

        self.twitch_auth = deps.twitch_auth
        self.twitch_api_service = deps.twitch_api_service
        self.joke_service = deps.joke_service
        self.minigame_service = deps.minigame_service
        self.user_cache = deps.user_cache
        self._background_runner = deps.background_runner
        self.minigame_orchestrator = MinigameOrchestrator(
            minigame_service=self.minigame_service,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            stream_service_factory=self._stream_service,
            get_used_words_use_case_factory=self._get_used_words_use_case,
            add_used_word_use_case_factory=self._add_used_word_use_case,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            llm_client=self._llm_client,
            system_prompt=self.SYSTEM_PROMPT_FOR_GROUP,
            prefix=self._prefix,
            command_guess_letter=self._COMMAND_GUESS_LETTER,
            command_guess_word=self._COMMAND_GUESS_WORD,
            command_guess=self._COMMAND_GUESS,
            command_rps=self._COMMAND_RPS,
            nick_provider=lambda: self.nick,
            split_text_fn=self.split_text,
            send_channel_message=self._send_channel_message
        )
        self._register_background_tasks()

        self._restore_stream_context()

        self.battle_waiting_user: str | None = None
        self.current_stream_summaries = []
        self.last_chat_summary_time = None
        self.roll_cooldowns = {}
        self._tasks_started = False
        self.telegram_bot = deps.telegram_bot

        # Command handlers (gradual extraction from monolith)
        self._followage_handler = FollowageCommandHandler(
            bot=self,
            chat_use_case_factory=self._chat_use_case,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            command_name=self._COMMAND_FOLLOWAGE,
            nick_provider=lambda: self.nick,
        )
        self._ask_handler = AskCommandHandler(
            intent_use_case=self._intent_use_case,
            prompt_service=self._prompt_service,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_GLADDI,
            prefix=self._prefix,
            source=self._SOURCE_TWITCH,
            generate_response_fn=self.generate_response_in_chat,
            post_message_fn=self._post_message_in_twitch_chat,
            nick_provider=lambda: self.nick,
        )
        self._battle_handler = BattleCommandHandler(
            bot=self,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            battle_use_case_factory=self._battle_use_case,
            equipment_service_factory=self._equipment_service,
            split_text_fn=self.split_text,
            timeout_fn=self._timeout_user,
            command_name=self._COMMAND_FIGHT,
            prefix=self._prefix,
            generate_response_fn=self.generate_response_in_chat,
            nick_provider=lambda: self.nick,
        )
        self._roll_handler = RollCommandHandler(
            economy_service_factory=self._economy_service,
            betting_service_factory=self._betting_service,
            equipment_service_factory=self._equipment_service,
            chat_use_case_factory=self._chat_use_case,
            roll_cooldowns=self.roll_cooldowns,
            cooldown_seconds=self._ROLL_COOLDOWN_SECONDS,
            split_text_fn=self.split_text,
            timeout_fn=self._timeout_user,
            command_name=self._COMMAND_ROLL,
            prefix=self._prefix,
            nick_provider=lambda: self.nick,
        )
        self._balance_handler = BalanceCommandHandler(
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_BALANCE,
            nick_provider=lambda: self.nick,
        )
        self._bonus_handler = BonusCommandHandler(
            stream_service_factory=self._stream_service,
            equipment_service_factory=self._equipment_service,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_BONUS,
            prefix=self._prefix,
            nick_provider=lambda: self.nick,
            split_text_fn=self.split_text,
        )
        self._transfer_handler = TransferCommandHandler(
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_TRANSFER,
            prefix=self._prefix,
            nick_provider=lambda: self.nick,
        )
        self._shop_handler = ShopCommandHandler(
            economy_service_factory=self._economy_service,
            equipment_service_factory=self._equipment_service,
            chat_use_case_factory=self._chat_use_case,
            command_shop=self._COMMAND_SHOP,
            command_buy=self._COMMAND_BUY,
            prefix=self._prefix,
            nick_provider=lambda: self.nick,
            split_text_fn=self.split_text,
        )

        # mutable holder for waiting user (so handler can mutate)
        self._battle_waiting_user_ref = {"value": None}

        logger.info("Twitch бот инициализирован успешно")

    def _chat_use_case(self, db):
        return self._deps.chat_use_case(db)

    def _battle_use_case(self, db):
        return self._deps.battle_use_case(db)

    def _ai_conversation_use_case(self, db):
        return self._deps.ai_conversation_use_case(db)

    def _betting_service(self, db):
        return self._deps.betting_service(db)

    def _economy_service(self, db):
        return self._deps.economy_service(db)

    def _equipment_service(self, db):
        return self._deps.equipment_service(db)

    def _get_used_words_use_case(self, db):
        return self._deps.get_used_words_use_case(db)

    def _add_used_word_use_case(self, db):
        return self._deps.add_used_word_use_case(db)

    def _stream_service(self, db):
        return self._deps.stream_service(db)

    def _start_new_stream_use_case(self, db):
        return self._deps.start_new_stream_use_case(db)

    def _viewer_service(self, db):
        return self._deps.viewer_service(db)

    async def _warmup_broadcaster_id(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст, пропускаем прогрев кеша ID")
                return

            channel_name = self.initial_channels[0]
            await self.user_cache.warmup(channel_name)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID канала: {e}")

    def _register_background_tasks(self):
        self._background_runner.register("post_joke", self.post_joke_periodically)
        self._background_runner.register("check_token", self.check_token_periodically)
        self._background_runner.register("check_stream_status", self.check_stream_status_periodically)
        self._background_runner.register("summarize_chat", self.summarize_chat_periodically)
        self._background_runner.register("check_minigames", self.check_minigames_periodically)
        self._background_runner.register("check_viewer_time", self.check_viewer_time_periodically)

    async def _start_background_tasks(self):
        if self._tasks_started:
            return

        self._background_runner.start_all()
        self._tasks_started = True

    async def close(self):
        await self._background_runner.cancel_all()
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
            active_stream = self._stream_service(db).get_active_stream(channel_name)
            if active_stream:
                self._viewer_service(db).update_viewer_session(active_stream.id, channel_name, nickname.lower(), datetime.utcnow())

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
        await self._followage_handler.handle(ctx)

    @commands.command(name=_COMMAND_GLADDI)
    async def ask(self, ctx):
        await self._ask_handler.handle(ctx)

    @commands.command(name=_COMMAND_FIGHT)
    async def battle(self, ctx):
        await self._battle_handler.handle(ctx, self._battle_waiting_user_ref)

    @commands.command(name=_COMMAND_ROLL)
    async def roll(self, ctx, amount: str = None):
        await self._roll_handler.handle(ctx, amount)
        self._cleanup_old_cooldowns()

    @commands.command(name=_COMMAND_BALANCE)
    async def balance(self, ctx):
        await self._balance_handler.handle(ctx)

    @commands.command(name=_COMMAND_BONUS)
    async def daily_bonus(self, ctx):
        await self._bonus_handler.handle(ctx)

    @commands.command(name=_COMMAND_TRANSFER)
    async def transfer_money(self, ctx, recipient: str = None, amount: str = None):
        await self._transfer_handler.handle(ctx, recipient, amount)

    @commands.command(name=_COMMAND_SHOP)
    async def shop(self, ctx):
        await self._shop_handler.handle_shop(ctx)

    @commands.command(name=_COMMAND_BUY)
    async def buy_item(self, ctx, *, item_name: str = None):
        await self._shop_handler.handle_buy(ctx, item_name)

    @commands.command(name=_COMMAND_EQUIPMENT)
    async def equipment(self, ctx):
        channel_name = ctx.channel.name
        user_name = ctx.author.display_name
        normalized_user_name = user_name.lower()

        logger.info(f"Команда {self._COMMAND_EQUIPMENT} от пользователя {user_name}")

        with db_ro_session() as db:
            equipment = self._equipment_service(db).get_user_equipment(channel_name, normalized_user_name)

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
            bot_choice, winning_choice, winners = self.minigame_service.finish_rps(game, channel_name)
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
        if game.user_choices and game.user_choices[normalized_user_name]:
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

            broadcaster_id = await self.user_cache.get_user_id(channel_name)
            moderator_id = await self.user_cache.get_user_id(self.nick)

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

    async def _send_channel_message(self, channel_name: str, message: str):
        """Отправляет сообщение в канал, разбивая его на части."""
        messages = self.split_text(message)
        channel = self.get_channel(channel_name)
        if not channel:
            logger.warning(f"Канал {channel_name} недоступен для отправки сообщения")
            return
        for msg in messages:
            await channel.send(msg)
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
                broadcaster_id = await self.user_cache.get_user_id(channel_name)

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

    async def check_stream_status_periodically(self):
        logger.info("Запуск периодической проверки статуса стрима")

        while True:
            try:
                if not self.initial_channels:
                    logger.warning("Список каналов пуст. Ожидание...")
                    await asyncio.sleep(self._CHECK_STREAM_STATUS_INTERVAL_SECONDS)
                    continue

                channel_name = self.initial_channels[0]
                broadcaster_id = await self.user_cache.get_user_id(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name}. Пропускаем проверку.")
                    await asyncio.sleep(self._CHECK_STREAM_STATUS_INTERVAL_SECONDS)
                    continue

                stream_status = await self.twitch_api_service.get_stream_status(broadcaster_id)

                if stream_status is None:
                    logger.error(f"Не удалось получить статус стрима для канала {channel_name}")
                    await asyncio.sleep(self._CHECK_STREAM_STATUS_INTERVAL_SECONDS)
                    continue

                game_name = None
                title = None
                if stream_status.is_online and stream_status.stream_data:
                    game_name = stream_status.stream_data.game_name
                    title = stream_status.stream_data.title

                logger.info(f"Статус стрима: {stream_status}")

                with db_ro_session() as db:
                    active_stream = self._stream_service(db).get_active_stream(channel_name)

                if stream_status.is_online and active_stream is None:
                    logger.info(f"Стрим начался: {game_name} - {title}")

                    try:
                        started_at = datetime.utcnow()
                        with SessionLocal.begin() as db:
                            start_stream_use_case = self._start_new_stream_use_case(db)
                            start_stream_use_case(channel_name, started_at, game_name, title)
                        self.minigame_service.set_stream_start_time(channel_name, started_at)
                        await self.stream_announcement(game_name, title, channel_name)
                        self.current_stream_summaries = []
                    except Exception as e:
                        logger.error(f"Ошибка при создании стрима: {e}")

                elif not stream_status.is_online and active_stream is not None:
                    logger.info("Стрим завершён")
                    finish_time = datetime.utcnow()

                    with SessionLocal.begin() as db:
                        self._stream_service(db).end_stream(active_stream.id, finish_time)
                        self._viewer_service(db).finish_stream_sessions(active_stream.id, finish_time)
                        total_viewers = self._viewer_service(db).get_unique_viewers_count(active_stream.id)
                        self._stream_service(db).update_stream_total_viewers(active_stream.id, total_viewers)
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
                            self._stream_service(db).update_stream_metadata(active_stream.id, game_name, title)
                        logger.info(f"Обновлены метаданные стрима: игра='{game_name}', название='{title}'")

            except Exception as e:
                logger.error(f"Ошибка в check_stream_status_periodically: {e}")

            await asyncio.sleep(self._CHECK_STREAM_STATUS_INTERVAL_SECONDS)

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
                broadcaster_id = await self.user_cache.get_user_id(channel_name)

                if not broadcaster_id:
                    logger.error(f"Не удалось получить ID канала {channel_name} для анализа чата")
                    continue

                with db_ro_session() as db:
                    active_stream = self._stream_service(db).get_active_stream(channel_name)
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
                delay = await self.minigame_orchestrator.run_tick(channel_name)
                await asyncio.sleep(delay)
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
                    active_stream = self._stream_service(db).get_active_stream(channel_name)

                if not active_stream:
                    await asyncio.sleep(self._CHECK_VIEWERS_INTERVAL_SECONDS)
                    continue

                with SessionLocal.begin() as db:
                    self._viewer_service(db).check_inactive_viewers(active_stream.id, datetime.utcnow())

                broadcaster_id = await self.user_cache.get_user_id(channel_name)
                moderator_id = await self.user_cache.get_user_id(self.nick)
                chatters = await self.twitch_api_service.get_stream_chatters(broadcaster_id, moderator_id)
                if chatters:
                    with SessionLocal.begin() as db:
                        self._viewer_service(db).update_viewers(active_stream.id, channel_name, chatters, datetime.utcnow())

                with db_ro_session() as db:
                    viewers_count = self._viewer_service(db).get_stream_watchers_count(active_stream.id)

                if viewers_count > active_stream.max_concurrent_viewers:
                    with SessionLocal.begin() as db:
                        self._stream_service(db).update_max_concurrent_viewers_count(active_stream.id, viewers_count)

                with SessionLocal.begin() as db:
                    viewer_sessions = self._viewer_service(db).get_stream_viewer_sessions(active_stream.id)
                    for session in viewer_sessions:
                        available_rewards = self._viewer_service(db).get_available_rewards(session)
                        for minutes_threshold, reward_amount in available_rewards:
                            claimed_list = session.get_claimed_rewards_list()
                            claimed_list.append(minutes_threshold)
                            rewards = ','.join(map(str, sorted(claimed_list)))
                            self._viewer_service(db).update_session_rewards(session.id, rewards, datetime.utcnow())
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
                active_stream = self._stream_service(db).get_active_stream(channel_name)

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
