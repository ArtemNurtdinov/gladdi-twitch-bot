from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_create import CreatePeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_patch import PatchPeriodicMessageDTO
from app.periodic_message.presentation.api.model.periodic_message_schema import PeriodicMessageSchema
from app.periodic_message.presentation.api.model.request.create_periodic_message_request import CreatePeriodicMessageRequest
from app.periodic_message.presentation.api.model.request.patch_periodic_message_request import PatchPeriodicMessageRequest


class PeriodicMessageSchemaMapper:
    def map_to_schema(self, dto: PeriodicMessageDTO) -> PeriodicMessageSchema:
        return PeriodicMessageSchema(
            id=dto.id,
            channel_name=dto.channel_name,
            content=dto.content,
            use_llm=dto.use_llm,
            interval_minutes=dto.interval_minutes,
            is_enabled=dto.is_enabled,
            last_sent_at=dto.last_sent_at,
            next_send_at=dto.next_send_at,
        )

    def map_create_to_dto(self, request: CreatePeriodicMessageRequest) -> CreatePeriodicMessageDTO:
        return CreatePeriodicMessageDTO(
            channel_name=request.channel_name,
            content=request.content,
            use_llm=request.use_llm,
            interval_minutes=request.interval_minutes,
            is_enabled=request.is_enabled,
        )

    def map_patch_to_dto(self, request: PatchPeriodicMessageRequest) -> PatchPeriodicMessageDTO:
        return PatchPeriodicMessageDTO(
            id=request.id,
            content=request.content,
            use_llm=request.use_llm,
            interval_minutes=request.interval_minutes,
            is_enabled=request.is_enabled,
        )
