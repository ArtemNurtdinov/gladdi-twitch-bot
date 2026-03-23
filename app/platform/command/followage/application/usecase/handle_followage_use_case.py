from app.ai.gen.application.use_cases.generate_response_use_case import GenerateResponseUseCase
from app.ai.gen.conversation.domain.conversation_repository import ConversationRepository
from app.chat.domain.model.chat_message import ChatMessage
from app.platform.command.followage.application.model import FollowageDTO
from app.platform.command.followage.application.uow import FollowAgeUnitOfWorkFactory
from core.provider import Provider


class HandleFollowAgeUseCase:
    def __init__(
        self,
        conversation_repo_provider: Provider[ConversationRepository],
        chat_response_use_case: GenerateResponseUseCase,
        unit_of_work_factory: FollowAgeUnitOfWorkFactory,
    ):
        self._conversation_repo_provider = conversation_repo_provider
        self._chat_response_use_case = chat_response_use_case
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(self, command_follow_age: FollowageDTO) -> str:
        channel_name = command_follow_age.channel_name
        user_message = command_follow_age.command_prefix + command_follow_age.command_name

        with self._unit_of_work_factory.create(read_only=True) as uow:
            follow_info = await uow.platform_repository.get_followage(
                channel_name=channel_name,
                user_name=command_follow_age.user_name,
            )

        if not follow_info:
            result = f"@{command_follow_age.display_name}, вы не отслеживаете канал."
            with self._unit_of_work_factory.create() as uow:
                uow.chat_repo.save(
                    ChatMessage(
                        channel_name=channel_name,
                        user_name=command_follow_age.user_name,
                        content=user_message,
                        created_at=command_follow_age.occurred_at,
                    )
                )
                uow.chat_repo.save(
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

        with self._unit_of_work_factory.create(read_only=True) as uow:
            system_prompt = uow.system_prompt_repository.get_system_prompt(channel_name)
            history = uow.conversation_service.get_last_messages(
                channel_name=command_follow_age.channel_name,
                system_prompt=system_prompt.prompt,
            )

        assistant_message = await self._chat_response_use_case.generate_response_from_history(history=history, prompt=prompt)

        with self._unit_of_work_factory.create() as uow:
            uow.conversation_service.save_conversation_to_db(
                channel_name=channel_name,
                user_message=prompt,
                ai_message=assistant_message,
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=channel_name,
                    user_name=command_follow_age.user_name,
                    content=user_message,
                    created_at=command_follow_age.occurred_at,
                )
            )
            uow.chat_repo.save(
                ChatMessage(
                    channel_name=channel_name,
                    user_name=command_follow_age.bot_nick.lower(),
                    content=assistant_message,
                    created_at=command_follow_age.occurred_at,
                )
            )
        return assistant_message
