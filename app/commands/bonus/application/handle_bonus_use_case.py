from app.commands.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.commands.bonus.application.model import BonusDTO


class HandleBonusUseCase:
    def __init__(
        self,
        unit_of_work_factory: BonusUnitOfWorkFactory,
    ):
        self._unit_of_work_factory = unit_of_work_factory

    async def handle(
        self,
        chat_context_dto: BonusDTO,
    ) -> str:
        user_message = chat_context_dto.command_prefix + chat_context_dto.command_name

        with self._unit_of_work_factory.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(chat_context_dto.channel_name)

        if not active_stream:
            result = f"🚫 @{chat_context_dto.display_name}, бонус доступен только во время стрима!"
        else:
            with self._unit_of_work_factory.create() as uow:
                user_equipment = uow.get_user_equipment_use_case.get_user_equipment(
                    channel_name=chat_context_dto.channel_name, user_name=chat_context_dto.user_name
                )
                bonus_result = uow.economy_policy.claim_daily_bonus(
                    active_stream_id=active_stream.id,
                    channel_name=chat_context_dto.channel_name,
                    user_name=chat_context_dto.user_name,
                    user_equipment=user_equipment,
                )
                if bonus_result.success:
                    if bonus_result.bonus_message:
                        result = (
                            f"🎁 @{chat_context_dto.display_name} получил бонус {bonus_result.bonus_amount} монет! "
                            f"{bonus_result.bonus_message}"
                        )
                    else:
                        result = f"🎁 @{chat_context_dto.display_name} получил бонус {bonus_result.bonus_amount} монет!"
                else:
                    if bonus_result.failure_reason == "already_claimed":
                        result = f"⏰ @{chat_context_dto.display_name}, бонус уже получен на этом стриме!"
                    elif bonus_result.failure_reason == "error":
                        result = f"❌ @{chat_context_dto.display_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                    else:
                        result = f"❌ @{chat_context_dto.display_name}, бонус недоступен!"

        with self._unit_of_work_factory.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=chat_context_dto.channel_name,
                user_name=chat_context_dto.user_name,
                content=user_message,
                current_time=chat_context_dto.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=chat_context_dto.channel_name,
                user_name=chat_context_dto.bot_nick,
                content=result,
                current_time=chat_context_dto.occurred_at,
            )

        return result
