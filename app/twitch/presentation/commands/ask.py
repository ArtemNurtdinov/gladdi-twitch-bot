from datetime import datetime

from sqlalchemy.orm import Session

from app.ai.application.conversation_service import ConversationService
from app.ai.application.intent_use_case import IntentUseCase
from app.ai.application.prompt_service import PromptService
from app.chat.application.chat_use_case import ChatUseCase
from core.db import SessionLocal
from typing import Callable, Awaitable, Any
from app.ai.domain.models import Intent


class AskCommandHandler:

    def __init__(
        self,
        command_prefix: str,
        command_name: str,
        intent_use_case: IntentUseCase,
        prompt_service: PromptService,
        ai_conversation_use_case_factory: Callable[[Session], ConversationService],
        chat_use_case_factory: Callable[[Session], ChatUseCase],
        generate_response_fn: Callable[[str, str], str],
        post_message_fn: Callable[[str, Any], Awaitable[None]],
        nick_provider: Callable[[], str],
    ):
        self.command_prefix = command_prefix
        self.command_name = command_name
        self.intent_use_case = intent_use_case
        self.prompt_service = prompt_service
        self._ai_conversation_use_case = ai_conversation_use_case_factory
        self._chat_use_case = chat_use_case_factory
        self.generate_response_in_chat = generate_response_fn
        self.post_message_fn = post_message_fn
        self.nick_provider = nick_provider

    async def handle(self, channel_name: str, full_message: str, display_name: str, ctx):
        user_message = full_message[len(f"{self.command_prefix}{self.command_name}"):].strip()

        intent = self.intent_use_case.get_intent_from_text(user_message)

        if intent == Intent.JACKBOX:
            prompt = self.prompt_service.get_jackbox_prompt(display_name, user_message)
        elif intent == Intent.SKUF_FEMBOY:
            prompt = self.prompt_service.get_skuf_femboy_prompt(display_name, user_message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self.prompt_service.get_dankar_cut_prompt(display_name, user_message)
        elif intent == Intent.HELLO:
            prompt = self.prompt_service.get_hello_prompt(display_name, user_message)
        else:
            prompt = self.prompt_service.get_default_prompt(display_name, user_message)

        result = self.generate_response_in_chat(prompt, channel_name)
        with SessionLocal.begin() as db:
            self._ai_conversation_use_case(db).save_conversation_to_db(channel_name, prompt, result)
            self._chat_use_case(db).save_chat_message(channel_name, self.nick_provider().lower(), result, datetime.utcnow())
        await self.post_message_fn(result, ctx)
