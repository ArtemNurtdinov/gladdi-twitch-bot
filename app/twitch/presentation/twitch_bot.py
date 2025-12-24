import asyncio
import logging
from typing import Optional

from twitchio.ext import commands

from app.ai.domain.models import AIMessage, Role
from app.twitch.bootstrap.deps import BotDependencies
from app.twitch.bootstrap.twitch_bot_settings import TwitchBotSettings, DEFAULT_SETTINGS
from app.twitch.presentation.background.bot_tasks import BotBackgroundTasks
from app.twitch.presentation.background.chat_summarizer_job import ChatSummaryState
from app.twitch.presentation.chat_event_service import ChatEventHandler
from core.db import db_ro_session

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

    def __init__(self, deps: BotDependencies, settings: TwitchBotSettings):
        self._settings = settings
        self._deps = deps

        self._prefix = self._settings.prefix
        self.initial_channels = [self._settings.channel_name]
        super().__init__(token=deps.twitch_auth.access_token, prefix=self._prefix, initial_channels=self.initial_channels)

        self._chat_summary_state = ChatSummaryState()
        self._battle_waiting_user_ref = {"value": None}

        self.minigame_orchestrator = None
        self._background_tasks: Optional[BotBackgroundTasks] = None
        self._command_registry = None
        self._chat_event_handler: ChatEventHandler | None = None

        logger.info("Twitch бот инициализирован успешно")

    @property
    def battle_waiting_user_ref(self):
        return self._battle_waiting_user_ref

    @property
    def chat_summary_state(self):
        return self._chat_summary_state

    def set_minigame_orchestrator(self, orchestrator):
        self.minigame_orchestrator = orchestrator

    def set_background_tasks(self, background_tasks: BotBackgroundTasks):
        self._background_tasks = background_tasks

    def set_command_registry(self, command_registry):
        self._command_registry = command_registry

    def set_chat_event_handler(self, chat_event_handler: ChatEventHandler):
        self._chat_event_handler = chat_event_handler

    async def _warmup_broadcaster_id(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст, пропускаем прогрев кеша ID")
                return

            channel_name = self.initial_channels[0]
            await self._deps.user_cache.warmup(channel_name)
        except Exception as e:
            logger.error(f"Не удалось прогреть кеш ID канала: {e}")

    async def _start_background_tasks(self):
        if not self._background_tasks:
            logger.warning("Фоновые задачи не сконфигурированы, пропускаем запуск")
            return
        self._background_tasks.start_all()

    async def close(self):
        if self._background_tasks:
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

        if message.content.startswith(self._prefix):
            await self.handle_commands(message)
            return

        if not self._chat_event_handler:
            logger.error("ChatEventHandler не сконфигурирован")
            return

        await self._chat_event_handler.handle(
            channel_name=message.channel.name,
            display_name=message.author.display_name,
            message=message.content,
            bot_nick=self.nick
        )

    @commands.command(name=DEFAULT_SETTINGS.command_followage)
    async def followage(self, ctx):
        await self._command_registry.followage.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_gladdi)
    async def ask(self, ctx):
        await self._command_registry.ask.handle(
            channel_name=ctx.channel.name,
            full_message=ctx.message.content,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_fight)
    async def battle(self, ctx):
        await self._command_registry.battle.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            battle_waiting_user_ref=self._battle_waiting_user_ref,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_roll)
    async def roll(self, ctx, amount: str = None):
        await self._command_registry.roll.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            amount=amount
        )

    @commands.command(name=DEFAULT_SETTINGS.command_balance)
    async def balance(self, ctx):
        await self._command_registry.balance.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_bonus)
    async def daily_bonus(self, ctx):
        await self._command_registry.bonus.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_transfer)
    async def transfer_money(self, ctx, recipient: str = None, amount: str = None):
        await self._command_registry.transfer.handle(
            channel_name=ctx.channel.name,
            sender_display_name=ctx.author.display_name,
            ctx=ctx,
            recipient=recipient,
            amount=amount
        )

    @commands.command(name=DEFAULT_SETTINGS.command_shop)
    async def shop(self, ctx):
        await self._command_registry.shop.handle_shop(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_buy)
    async def buy_item(self, ctx, *, item_name: str = None):
        await self._command_registry.shop.handle_buy(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            item_name=item_name
        )

    @commands.command(name=DEFAULT_SETTINGS.command_equipment)
    async def equipment(self, ctx):
        await self._command_registry.equipment.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_top)
    async def top_users(self, ctx):
        await self._command_registry.top_bottom.handle_top(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_bottom)
    async def bottom_users(self, ctx):
        await self._command_registry.top_bottom.handle_bottom(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_help)
    async def list_commands(self, ctx):
        await self._command_registry.help.handle(
            channel_name=ctx.channel.name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_stats)
    async def user_stats(self, ctx):
        await self._command_registry.stats.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx
        )

    @commands.command(name=DEFAULT_SETTINGS.command_guess)
    async def guess_number(self, ctx, number: str = None):
        await self._command_registry.guess.handle_guess_number(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            number=number
        )

    @commands.command(name=DEFAULT_SETTINGS.command_guess_letter)
    async def guess_letter(self, ctx, letter: str = None):
        await self._command_registry.guess.handle_guess_letter(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            letter=letter
        )

    @commands.command(name=DEFAULT_SETTINGS.command_guess_word)
    async def guess_word(self, ctx, *, word: str = None):
        await self._command_registry.guess.handle_guess_word(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            word=word
        )

    @commands.command(name=DEFAULT_SETTINGS.command_rps)
    async def join_rps(self, ctx, choice: str = None):
        await self._command_registry.rps.handle(
            channel_name=ctx.channel.name,
            display_name=ctx.author.display_name,
            ctx=ctx,
            choice=choice
        )

    async def timeout_user(self, channel_name: str, username: str, duration_seconds: int, reason: str):
        try:
            user = await self._deps.twitch_api_service.get_user_by_login(username)
            user_id = None if user is None else user.id

            broadcaster_id = await self._deps.user_cache.get_user_id(channel_name)
            moderator_id = await self._deps.user_cache.get_user_id(self.nick)

            if not user_id:
                logger.error(f"Не удалось получить ID пользователя {username}")
                return
            if not broadcaster_id:
                logger.error(f"Не удалось получить ID канала {channel_name}")
                return
            if not moderator_id:
                logger.error(f"Не удалось получить ID модератора {self.nick}")
                return

            success = await self._deps.twitch_api_service.timeout_user(broadcaster_id, moderator_id, user_id, duration_seconds, reason)

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

    async def post_message_in_twitch_chat(self, message: str, ctx):
        messages = self._split_text(message)

        for msg in messages:
            await ctx.send(msg)
            await asyncio.sleep(0.3)

    async def send_channel_message(self, channel_name: str, message: str):
        channel = self.get_channel(channel_name)
        if not channel:
            logger.warning(f"Канал {channel_name} недоступен для отправки сообщения")
            return

        messages = self._split_text(message)
        for msg in messages:
            await channel.send(msg)
            await asyncio.sleep(0.3)

    def restore_stream_context(self):
        try:
            if not self.initial_channels:
                logger.warning("Список каналов пуст при восстановлении контекста стрима")
                return

            channel_name = self.initial_channels[0]
            with db_ro_session() as db:
                active_stream = self._deps.stream_service(db).get_active_stream(channel_name)

            if active_stream:
                self._deps.minigame_service.set_stream_start_time(channel_name, active_stream.started_at)
                logger.info(f"Найден активный стрим ID {active_stream.id}")
            else:
                logger.info("Активных стримов не найдено")
        except Exception as e:
            logger.error(f"Ошибка при восстановлении состояния стрима: {e}")

    def generate_response_in_chat(self, prompt: str, channel_name: str) -> str:
        messages = []
        with db_ro_session() as db:
            last_messages = self._deps.ai_conversation_use_case(db).get_last_messages(channel_name, self.SYSTEM_PROMPT_FOR_GROUP)
        messages.extend(last_messages)
        messages.append(AIMessage(Role.USER, prompt))
        assistant_message = self._deps.llm_client.generate_ai_response(messages)
        return assistant_message
