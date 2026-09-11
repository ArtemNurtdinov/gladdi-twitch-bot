from datetime import UTC, datetime, timedelta

from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.common.infrastructure.db.session_scoped_factory import SessionScopedFactory
from app.common.infrastructure.db.types import SessionFactory
from app.periodic_message.application.model.post_periodic_messages import PostPeriodicMessagesDTO
from app.periodic_message.application.model.prepared_periodic_message import PreparedPeriodicMessage
from app.periodic_message.application.uow.periodic_message_uow import PeriodicMessageUnitOfWorkFactory


class HandlePostPeriodicMessagesUseCase:
    def __init__(
        self,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        periodic_message_uow: PeriodicMessageUnitOfWorkFactory,
        db_ro_session: SessionFactory,
    ):
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._periodic_message_uow = periodic_message_uow
        self._db_ro_session = db_ro_session

    async def handle(self, payload: PostPeriodicMessagesDTO) -> list[PreparedPeriodicMessage]:
        now = datetime.now(UTC)

        with self._periodic_message_uow.create(read_only=True) as uow:
            active_stream = uow.stream_repository.get_active_stream(payload.channel_name)
            if not active_stream:
                return []
            due_messages = uow.periodic_message_repository.get_due_enabled(payload.channel_name, now)

        if not due_messages:
            return []

        prepared: list[PreparedPeriodicMessage] = []

        for message in due_messages:
            if message.use_llm:
                with self._db_ro_session() as session:
                    text = await self._generate_response_use_case_factory.get(session).generate_response(
                        prompt=message.content, channel_name=payload.channel_name
                    )
            else:
                text = message.content

            prepared.append(
                PreparedPeriodicMessage(
                    message_id=message.id,
                    text=text,
                    interval_minutes=message.interval_minutes,
                    use_llm=message.use_llm,
                    prompt=message.content,
                )
            )

        return prepared

    async def mark_sent(
        self,
        *,
        message_id: int,
        interval_minutes: int,
        channel_name: str,
        bot_nick: str,
        text: str,
        use_llm: bool,
        prompt: str,
        occurred_at: datetime,
    ) -> None:
        sent_at = datetime.now(UTC)
        next_send_at = sent_at + timedelta(minutes=interval_minutes)

        with self._periodic_message_uow.create() as uow:
            if use_llm:
                uow.conversation_service.save_conversation_to_db(
                    channel_name=channel_name,
                    user_message=prompt,
                    ai_message=text,
                )
            uow.chat_use_case.save_chat_message(
                channel_name=channel_name,
                user_name=bot_nick,
                content=text,
                current_time=occurred_at,
            )
            await uow.periodic_message_repository.update_schedule(
                message_id=message_id,
                last_sent_at=sent_at,
                next_send_at=next_send_at,
            )
