import logging
from datetime import datetime

from core.db import SessionLocal
from typing import Callable
from app.ai.domain.models import Intent

logger = logging.getLogger(__name__)


class AskCommandHandler:

    def __init__(
        self,
        intent_use_case,
        prompt_service,
        ai_conversation_use_case_factory,
        chat_use_case_factory,
        command_name: str,
        prefix: str,
        source: str,
        generate_response_fn,
        post_message_fn,
        nick_provider: Callable[[], str],
    ):
        self.intent_use_case = intent_use_case
        self.prompt_service = prompt_service
        self._ai_conversation_use_case = ai_conversation_use_case_factory
        self._chat_use_case = chat_use_case_factory
        self.command_name = command_name
        self.prefix = prefix
        self.source = source
        self.generate_response_in_chat = generate_response_fn
        self.post_message_fn = post_message_fn
        self.nick_provider = nick_provider

    async def handle(self, ctx):
        channel_name = ctx.channel.name
        full_message = ctx.message.content
        question = full_message[len(f"{self.prefix}{self.command_name}"):].strip()
        nickname = ctx.author.display_name
        bot_nick = self.nick_provider() or ""

        logger.info(f"Команда от пользователя {nickname}")

        intent = self.intent_use_case.get_intent_from_text(question)
        logger.info(f"Определён интент: {intent}")

        if intent == Intent.JACKBOX:
            prompt = self.prompt_service.get_jackbox_prompt(self.source, nickname, question)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self.prompt_service.get_skuf_femboy_prompt(self.source, nickname, question)
        elif intent == Intent.DANKAR_CUT:
            prompt = self.prompt_service.get_dankar_cut_prompt(self.source, nickname, question)
        elif intent == Intent.HELLO:
            prompt = self.prompt_service.get_hello_prompt(self.source, nickname, question)
        else:
            prompt = self.prompt_service.get_default_prompt(self.source, nickname, question)

        result = self.generate_response_in_chat(prompt, channel_name)
        with SessionLocal.begin() as db:
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            self._chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
        logger.info(f"Отправлен ответ пользователю {nickname}")
        await self.post_message_fn(result, ctx)
