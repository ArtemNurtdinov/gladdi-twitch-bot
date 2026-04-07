from app.ai.gen.llm.application.usecase.generate_response_use_case import GenerateResponseUseCase
from app.chat.domain.model.chat_message import ChatMessage
from app.core.common.session.session_scoped_factory import SessionScopedFactory
from app.platform.command.followage.application.model import FollowageDTO
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from core.types import SessionFactory


class HandleFollowAgeUseCase:
    def __init__(
        self,
        generate_response_use_case_factory: SessionScopedFactory[GenerateResponseUseCase],
        follow_age_uow_factory: FollowAgeUnitOfWorkFactory,
        session_factory_ro: SessionFactory,
    ):
        self._generate_response_use_case_factory = generate_response_use_case_factory
        self._follow_age_uow_factory = follow_age_uow_factory
        self._db_ro_session = session_factory_ro

    async def handle(self, command_follow_age: FollowageDTO) -> str:
        channel_name = command_follow_age.channel_name

        with self._follow_age_uow_factory.create(read_only=True) as uow:
            follow_info = await uow.platform_repository.get_followage(
                channel_name=channel_name,
                user_name=command_follow_age.user_name,
            )

        if not follow_info:
            result = f"@{command_follow_age.display_name}, вы не отслеживаете канал."
            with self._follow_age_uow_factory.create() as uow:
                uow.chat_repository.save(
                    ChatMessage(
                        channel_name=channel_name,
                        user_name=command_follow_age.user_name,
                        content=command_follow_age.message,
                        created_at=command_follow_age.occurred_at,
                    )
                )
                uow.chat_repository.save(
                    ChatMessage(
                        channel_name=channel_name,
                        user_name=command_follow_age.bot_nick.lower(),
                        content=result,
                        created_at=command_follow_age.occurred_at,
                    )
                )
            return result

        follow_duration = command_follow_age.occurred_at - follow_info.followed_at

        days = follow_duration.days
        hours, remainder = divmod(follow_duration.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        prompt = (
            f"Пользователь @{command_follow_age.display_name} отслеживает канал уже {days} дней, {hours} часов и {minutes} минут. "
            f"Сообщи ему об этом кратко и оригинально."
        )

        with self._db_ro_session() as session:
            assistant_message = await self._generate_response_use_case_factory.get(session).generate_response(
                prompt=prompt, channel_name=channel_name
            )

        with self._follow_age_uow_factory.create() as uow:
            uow.conversation_service.save_conversation_to_db(
                channel_name=channel_name,
                user_message=prompt,
                ai_message=assistant_message,
            )
            uow.chat_repository.save(
                ChatMessage(
                    channel_name=channel_name,
                    user_name=command_follow_age.user_name,
                    content=command_follow_age.message,
                    created_at=command_follow_age.occurred_at,
                )
            )
            uow.chat_repository.save(
                ChatMessage(
                    channel_name=channel_name,
                    user_name=command_follow_age.bot_nick.lower(),
                    content=assistant_message,
                    created_at=command_follow_age.occurred_at,
                )
            )
        return assistant_message
