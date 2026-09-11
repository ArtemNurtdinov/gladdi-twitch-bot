from app.periodic_message.application.mapper.periodic_message_mapper import PeriodicMessageMapper
from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_patch import PatchPeriodicMessageDTO
from app.periodic_message.domain.repository import PeriodicMessageRepository


class PatchPeriodicMessageUseCase:
    def __init__(self, repository: PeriodicMessageRepository, mapper: PeriodicMessageMapper):
        self._repository = repository
        self._mapper = mapper

    async def patch(self, dto: PatchPeriodicMessageDTO) -> PeriodicMessageDTO | None:
        updated = await self._repository.patch(self._mapper.map_patch_to_domain(dto))
        if updated is None:
            return None
        return self._mapper.to_dto(updated)
