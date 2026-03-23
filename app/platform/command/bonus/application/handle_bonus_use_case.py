from app.platform.command.bonus.application.bonus_uow import BonusUnitOfWorkFactory
from app.platform.command.bonus.application.model import BonusDTO


class HandleBonusUseCase:
    def __init__(self, bonus_uow: BonusUnitOfWorkFactory):
        self._bonus_uow = bonus_uow

    async def handle(self, bonus: BonusDTO) -> str:
        user_message = bonus.command_prefix + bonus.command_name

        with self._bonus_uow.create(read_only=True) as uow:
            active_stream = uow.stream_service.get_active_stream(bonus.channel_name)

        if not active_stream:
            result = f"🚫 @{bonus.display_name}, бонус доступен только во время стрима!"
            with self._bonus_uow.create() as uow:
                uow.chat_use_case.save_chat_message(
                    channel_name=bonus.channel_name,
                    user_name=bonus.user_name,
                    content=user_message,
                    current_time=bonus.occurred_at,
                )
                uow.chat_use_case.save_chat_message(
                    channel_name=bonus.channel_name,
                    user_name=bonus.bot_nick,
                    content=result,
                    current_time=bonus.occurred_at,
                )

            return result

        with self._bonus_uow.create() as uow:
            user_equipment = uow.get_user_equipment_use_case.get_user_equipment(channel_name=bonus.channel_name, user_name=bonus.user_name)
            bonus_result = uow.economy_policy.claim_daily_bonus(
                active_stream_id=active_stream.id,
                channel_name=bonus.channel_name,
                user_name=bonus.user_name,
                user_equipment=user_equipment,
            )
            if bonus_result.success:
                if bonus_result.bonus_message:
                    result = f"🎁 @{bonus.display_name} получил бонус {bonus_result.bonus_amount} монет! {bonus_result.bonus_message}"
                else:
                    result = f"🎁 @{bonus.display_name} получил бонус {bonus_result.bonus_amount} монет!"
            else:
                if bonus_result.failure_reason == "already_claimed":
                    result = f"⏰ @{bonus.display_name}, бонус уже получен на этом стриме!"
                elif bonus_result.failure_reason == "error":
                    result = f"❌ @{bonus.display_name}, произошла ошибка при получении бонуса. Попробуй позже!"
                else:
                    result = f"❌ @{bonus.display_name}, бонус недоступен!"

        with self._bonus_uow.create() as uow:
            uow.chat_use_case.save_chat_message(
                channel_name=bonus.channel_name,
                user_name=bonus.user_name,
                content=user_message,
                current_time=bonus.occurred_at,
            )
            uow.chat_use_case.save_chat_message(
                channel_name=bonus.channel_name,
                user_name=bonus.bot_nick,
                content=result,
                current_time=bonus.occurred_at,
            )

        return result
