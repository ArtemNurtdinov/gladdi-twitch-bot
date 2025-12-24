from datetime import datetime
from typing import Callable, Awaitable

from app.ai.domain.models import Intent
from app.twitch.bootstrap.deps import BotDependencies
from core.db import SessionLocal
import logging

logger = logging.getLogger(__name__)


class ChatEventService:
    def __init__(
        self,
        deps: BotDependencies,
        generate_response_fn: Callable[[str, str], str],
        send_channel_message: Callable[[str, str], Awaitable[None]]
    ):
        self._deps = deps
        self._generate_response_fn = generate_response_fn
        self._send_channel_message = send_channel_message

    async def handle(self, channel_name: str, display_name: str, message: str, bot_nick: str):
        normalized_user_name = display_name.lower()

        with SessionLocal.begin() as db:
            self._deps.chat_use_case(db).save_chat_message(channel_name, normalized_user_name, message, datetime.utcnow())
            self._deps.economy_service(db).process_user_message_activity(channel_name, normalized_user_name)
            active_stream = self._deps.stream_service(db).get_active_stream(channel_name)
            if active_stream:
                self._deps.viewer_service(db).update_viewer_session(active_stream.id, channel_name, normalized_user_name, datetime.utcnow())

        intent = self._deps.intent_use_case.get_intent_from_text(message)
        logger.info(f"Определён интент: {intent}")

        prompt = None

        if intent == Intent.JACKBOX:
            prompt = self._deps.prompt_service.get_jackbox_prompt(display_name, message)
        elif intent == Intent.DANKAR_CUT:
            prompt = self._deps.prompt_service.get_dankar_cut_prompt(display_name, message)
        elif intent == Intent.HELLO:
            prompt = self._deps.prompt_service.get_hello_prompt(display_name, message)

        if prompt is None:
            return

        result = self._generate_response_fn(prompt, channel_name)
        await self._send_channel_message(channel_name, result)
        with SessionLocal.begin() as db:
            self._deps.chat_use_case(db).save_chat_message(channel_name, bot_nick.lower(), result, datetime.utcnow())
