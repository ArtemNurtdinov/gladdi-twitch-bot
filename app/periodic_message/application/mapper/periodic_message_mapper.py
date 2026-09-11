from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_create import CreatePeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_patch import PatchPeriodicMessageDTO
from app.periodic_message.domain.model.periodic_message import PeriodicMessage, PeriodicMessageCreate, PeriodicMessagePatch


class PeriodicMessageMapper:
    def to_dto(self, message: PeriodicMessage) -> PeriodicMessageDTO:
        return PeriodicMessageDTO(
            id=message.id,
            channel_name=message.channel_name,
            content=message.content,
            use_llm=message.use_llm,
            interval_minutes=message.interval_minutes,
            is_enabled=message.is_enabled,
            last_sent_at=message.last_sent_at,
            next_send_at=message.next_send_at,
        )

    def map_create_to_domain(self, dto: CreatePeriodicMessageDTO) -> PeriodicMessageCreate:
        return PeriodicMessageCreate(
            channel_name=dto.channel_name,
            content=dto.content,
            use_llm=dto.use_llm,
            interval_minutes=dto.interval_minutes,
            is_enabled=dto.is_enabled,
        )

    def map_patch_to_domain(self, dto: PatchPeriodicMessageDTO) -> PeriodicMessagePatch:
        return PeriodicMessagePatch(
            id=dto.id,
            content=dto.content,
            use_llm=dto.use_llm,
            interval_minutes=dto.interval_minutes,
            is_enabled=dto.is_enabled,
        )
