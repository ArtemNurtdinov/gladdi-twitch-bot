from datetime import datetime
from typing import Any, Callable

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.chat.application.chat_use_case import ChatUseCase
from core.db import SessionLocal


class FollowageCommandHandler:

    def __init__(
        self,
        bot: Any,
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        command_name: str,
        nick_provider: Callable[[], str],
    ):
        self.bot = bot
        self.twitch_api_service = bot.twitch_api_service
        self._chat_use_case = chat_use_case_factory
        self._ai_conversation_use_case = ai_conversation_use_case_factory
        self.generate_response_in_chat = bot.generate_response_in_chat
        self.command_name = command_name
        self.nick_provider = nick_provider

    async def handle(self, ctx):
        if not ctx.author:
            return

        user_name = ctx.author.name
        channel_name = ctx.channel.name

        broadcaster = await self.twitch_api_service.get_user_by_login(channel_name)
        broadcaster_id = None if broadcaster is None else broadcaster.id

        if not broadcaster_id:
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
            prompt = (
                f"@{user_name} отслеживает канал {channel_name} уже {days} дней, {hours} часов и {minutes} минут. "
                f"Сообщи ему об этом как-нибудь оригинально."
            )
            result = self.generate_response_in_chat(prompt, channel_name)
            with SessionLocal.begin() as db:
                self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
        else:
            result = f'@{user_name}, вы не отслеживаете канал {channel_name}.'
            with SessionLocal.begin() as db:
                bot_nick = self.nick_provider() or ""
                self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
            await ctx.send(result)
