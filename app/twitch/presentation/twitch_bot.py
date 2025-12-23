import asyncio
import logging
from twitchio.ext import commands
from datetime import datetime

from app.ai.domain.models import Intent, AIMessage, Role
from app.minigame.application.minigame_orchestrator import MinigameOrchestrator
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.presentation.commands.ask import AskCommandHandler
from app.twitch.presentation.commands.battle import BattleCommandHandler
from app.twitch.presentation.commands.balance import BalanceCommandHandler
from app.twitch.presentation.commands.bonus import BonusCommandHandler
from app.twitch.presentation.commands.equipment import EquipmentCommandHandler
from app.twitch.presentation.commands.followage import FollowageCommandHandler
from app.twitch.presentation.commands.guess import GuessCommandHandler
from app.twitch.presentation.commands.help import HelpCommandHandler
from app.twitch.presentation.commands.roll import RollCommandHandler
from app.twitch.presentation.commands.rps import RpsCommandHandler
from app.twitch.presentation.commands.shop import ShopCommandHandler
from app.twitch.presentation.commands.stats import StatsCommandHandler
from app.twitch.presentation.commands.top_bottom import TopBottomCommandHandler
from app.twitch.presentation.commands.transfer import TransferCommandHandler
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.chat_summarizer_job import ChatSummaryState
from app.twitch.presentation.background.post_joke_job import PostJokeJob
from app.twitch.presentation.background.token_checker_job import TokenCheckerJob
from app.twitch.presentation.background.stream_status_job import StreamStatusJob
from app.twitch.presentation.background.chat_summarizer_job import ChatSummarizerJob
from app.twitch.presentation.background.minigame_tick_job import MinigameTickJob
from app.twitch.presentation.background.viewer_time_job import ViewerTimeJob
from core.config import config
from core.db import db_ro_session, SessionLocal

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
    _CHECK_VIEWERS_INTERVAL_SECONDS = 10
    _CHECK_STREAM_STATUS_INTERVAL_SECONDS = 60
    _CHANNEL_NAME = "artemnefrit"

    def __init__(self, deps: BotDependencies):
        self._deps = deps
        self._prefix = '!'
        self.initial_channels = [self._CHANNEL_NAME]
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
        self.telegram_bot = deps.telegram_bot
        self._chat_summary_state = ChatSummaryState()
        self.roll_cooldowns = {}
        self.battle_waiting_user: str | None = None

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
            bot_nick_provider=lambda: self.nick,
            send_channel_message=self._send_channel_message
        )
        self._background_tasks = BotBackgroundTasks(
            runner=self._background_runner,
            jobs=[
                PostJokeJob(
                    channel_name=self._CHANNEL_NAME,
                    joke_service=self.joke_service,
                    user_cache=self.user_cache,
                    twitch_api_service=self.twitch_api_service,
                    generate_response_in_chat=self.generate_response_in_chat,
                    ai_conversation_use_case_factory=self._ai_conversation_use_case,
                    chat_use_case_factory=self._chat_use_case,
                    send_channel_message=self._send_channel_message,
                    bot_nick_provider=lambda: self.nick,
                ),
                TokenCheckerJob(twitch_auth=self.twitch_auth),
                StreamStatusJob(
                    channel_name=self._CHANNEL_NAME,
                    user_cache=self.user_cache,
                    twitch_api_service=self.twitch_api_service,
                    stream_service_factory=self._stream_service,
                    start_new_stream_use_case_factory=self._start_new_stream_use_case,
                    viewer_service_factory=self._viewer_service,
                    battle_use_case_factory=self._battle_use_case,
                    economy_service_factory=self._economy_service,
                    chat_use_case_factory=self._chat_use_case,
                    ai_conversation_use_case_factory=self._ai_conversation_use_case,
                    minigame_service=self.minigame_service,
                    telegram_bot=self.telegram_bot,
                    group_id=self._GROUP_ID,
                    generate_response_in_chat=self.generate_response_in_chat,
                    state=self._chat_summary_state,
                    stream_status_interval_seconds=self._CHECK_STREAM_STATUS_INTERVAL_SECONDS,
                ),
                ChatSummarizerJob(
                    channel_name=self._CHANNEL_NAME,
                    user_cache=self.user_cache,
                    twitch_api_service=self.twitch_api_service,
                    stream_service_factory=self._stream_service,
                    chat_use_case_factory=self._chat_use_case,
                    generate_response_in_chat=self.generate_response_in_chat,
                    state=self._chat_summary_state,
                ),
                MinigameTickJob(
                    channel_name=self._CHANNEL_NAME,
                    minigame_orchestrator=self.minigame_orchestrator,
                ),
                ViewerTimeJob(
                    channel_name=self._CHANNEL_NAME,
                    viewer_service_factory=self._viewer_service,
                    stream_service_factory=self._stream_service,
                    economy_service_factory=self._economy_service,
                    user_cache=self.user_cache,
                    twitch_api_service=self.twitch_api_service,
                    bot_nick_provider=lambda: self.nick,
                    check_interval_seconds=self._CHECK_VIEWERS_INTERVAL_SECONDS,
                ),
            ],
        )

        self._restore_stream_context()

        self._followage_handler = FollowageCommandHandler(
            chat_use_case_factory=self._chat_use_case,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            command_name=self._COMMAND_FOLLOWAGE,
            bot_nick_provider=lambda: self.nick,
            generate_response_fn=self.generate_response_in_chat,
            twitch_api_service=self.twitch_api_service,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._ask_handler = AskCommandHandler(
            command_prefix=self._prefix,
            command_name=self._COMMAND_GLADDI,
            intent_use_case=self._intent_use_case,
            prompt_service=self._prompt_service,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            chat_use_case_factory=self._chat_use_case,
            generate_response_fn=self.generate_response_in_chat,
            post_message_fn=self._post_message_in_twitch_chat,
            bot_nick_provider=lambda: self.nick
        )
        self._battle_handler = BattleCommandHandler(
            command_prefix=self._prefix,
            command_name=self._COMMAND_FIGHT,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            ai_conversation_use_case_factory=self._ai_conversation_use_case,
            battle_use_case_factory=self._battle_use_case,
            equipment_service_factory=self._equipment_service,
            timeout_fn=self._timeout_user,
            generate_response_fn=self.generate_response_in_chat,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._roll_handler = RollCommandHandler(
            command_prefix=self._prefix,
            command_name=self._COMMAND_ROLL,
            economy_service_factory=self._economy_service,
            betting_service_factory=self._betting_service,
            equipment_service_factory=self._equipment_service,
            chat_use_case_factory=self._chat_use_case,
            roll_cooldowns=self.roll_cooldowns,
            cooldown_seconds=self._ROLL_COOLDOWN_SECONDS,
            timeout_fn=self._timeout_user,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._balance_handler = BalanceCommandHandler(
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._bonus_handler = BonusCommandHandler(
            command_prefix=self._prefix,
            command_name=self._COMMAND_BONUS,
            stream_service_factory=self._stream_service,
            equipment_service_factory=self._equipment_service,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._transfer_handler = TransferCommandHandler(
            command_prefix=self._prefix,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_TRANSFER,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._shop_handler = ShopCommandHandler(
            command_prefix=self._prefix,
            command_shop_name=self._COMMAND_SHOP,
            command_buy_name=self._COMMAND_BUY,
            economy_service_factory=self._economy_service,
            equipment_service_factory=self._equipment_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._equipment_handler = EquipmentCommandHandler(
            command_prefix=self._prefix,
            command_name=self._COMMAND_EQUIPMENT,
            command_shop=self._COMMAND_SHOP,
            equipment_service_factory=self._equipment_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._top_bottom_handler = TopBottomCommandHandler(
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            command_top=self._COMMAND_TOP,
            command_bottom=self._COMMAND_BOTTOM,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._stats_handler = StatsCommandHandler(
            economy_service_factory=self._economy_service,
            betting_service_factory=self._betting_service,
            battle_use_case_factory=self._battle_use_case,
            chat_use_case_factory=self._chat_use_case,
            command_name=self._COMMAND_STATS,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        commands = {
            self._COMMAND_BALANCE,
            self._COMMAND_BONUS,
            f"{self._COMMAND_ROLL} [сумма]",
            f"{self._COMMAND_TRANSFER} @ник сумма",
            self._COMMAND_SHOP,
            f"{self._COMMAND_BUY} название",
            self._COMMAND_EQUIPMENT,
            self._COMMAND_TOP,
            self._COMMAND_BOTTOM,
            self._COMMAND_STATS,
            self._COMMAND_FIGHT,
            f"{self._COMMAND_GLADDI} текст",
            self._COMMAND_FOLLOWAGE,
        }
        self._help_handler = HelpCommandHandler(
            command_prefix=self._prefix,
            chat_use_case_factory=self._chat_use_case,
            commands=commands,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._guess_handler = GuessCommandHandler(
            command_prefix=self._prefix,
            command_guess=self._COMMAND_GUESS,
            command_guess_letter=self._COMMAND_GUESS_LETTER,
            command_guess_word=self._COMMAND_GUESS_WORD,
            minigame_service=self.minigame_service,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )
        self._rps_handler = RpsCommandHandler(
            minigame_service=self.minigame_service,
            economy_service_factory=self._economy_service,
            chat_use_case_factory=self._chat_use_case,
            bot_nick_provider=lambda: self.nick,
            post_message_fn=self._post_message_in_twitch_chat
        )

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

    async def _start_background_tasks(self):
        self._background_tasks.start_all()

    async def close(self):
        await self._background_tasks.stop_all()
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
            prompt = self._prompt_service.get_jackbox_prompt(nickname, content)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._prompt_service.get_dankar_cut_prompt(nickname, content)
        elif intent == Intent.HELLO:
            prompt = self._prompt_service.get_hello_prompt(nickname, content)

        if prompt is not None:
            result = self.generate_response_in_chat(prompt, channel_name)
            await self._post_message_in_twitch_chat(result, message.channel)
            with SessionLocal.begin() as db:
                self._chat_use_case(db).save_chat_message(channel_name, self.nick.lower(), result, datetime.utcnow())
            logger.info(f"Отправлен ответ на сообщение от {nickname}")

    @commands.command(name=_COMMAND_FOLLOWAGE)
    async def followage(self, ctx):
        await self._followage_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_GLADDI)
    async def ask(self, ctx):
        await self._ask_handler.handle(
            channel_name=ctx.channel.name,
            full_message=ctx.message.content,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_FIGHT)
    async def battle(self, ctx):
        await self._battle_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            battle_waiting_user_ref=self._battle_waiting_user_ref,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_ROLL)
    async def roll(self, ctx, amount: str = None):
        await self._roll_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            amount=amount
        )
        self._cleanup_old_cooldowns()

    @commands.command(name=_COMMAND_BALANCE)
    async def balance(self, ctx):
        await self._balance_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_BONUS)
    async def daily_bonus(self, ctx):
        await self._bonus_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_TRANSFER)
    async def transfer_money(self, ctx, recipient: str = None, amount: str = None):
        await self._transfer_handler.handle(
            channel_name=ctx.channel.name,
            sender_display_name=ctx.author.display_name,
            ctx=ctx,
            recipient=recipient,
            amount=amount
        )

    @commands.command(name=_COMMAND_SHOP)
    async def shop(self, ctx):
        await self._shop_handler.handle_shop(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_BUY)
    async def buy_item(self, ctx, *, item_name: str = None):
        await self._shop_handler.handle_buy(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            item_name=item_name
        )

    @commands.command(name=_COMMAND_EQUIPMENT)
    async def equipment(self, ctx):
        await self._equipment_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_TOP)
    async def top_users(self, ctx):
        await self._top_bottom_handler.handle_top(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_BOTTOM)
    async def bottom_users(self, ctx):
        await self._top_bottom_handler.handle_bottom(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_HELP)
    async def list_commands(self, ctx):
        await self._help_handler.handle(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_STATS)
    async def user_stats(self, ctx):
        await self._stats_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=_COMMAND_GUESS)
    async def guess_number(self, ctx, number: str = None):
        await self._guess_handler.handle_guess_number(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            number=number
        )

    @commands.command(name=_COMMAND_GUESS_LETTER)
    async def guess_letter(self, ctx, letter: str = None):
        await self._guess_handler.handle_guess_letter(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            letter=letter
        )

    @commands.command(name=_COMMAND_GUESS_WORD)
    async def guess_word(self, ctx, *, word: str = None):
        await self._guess_handler.handle_guess_word(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            word=word
        )

    @commands.command(name=_COMMAND_RPS)
    async def join_rps(self, ctx, choice: str = None):
        await self._rps_handler.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            choice=choice
        )

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

    def _split_text(self, text, max_length=500):
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
        messages = self._split_text(message)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def _send_channel_message(self, channel_name: str, message: str):
        messages = self._split_text(message)
        channel = self.get_channel(channel_name)
        if not channel:
            logger.warning(f"Канал {channel_name} недоступен для отправки сообщения")
            return
        for msg in messages:
            await channel.send(msg)
            await asyncio.sleep(0.3)

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
