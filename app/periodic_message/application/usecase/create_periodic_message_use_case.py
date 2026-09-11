from app.periodic_message.application.mapper.periodic_message_mapper import PeriodicMessageMapper
from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.application.model.periodic_message_create import CreatePeriodicMessageDTO
from app.periodic_message.domain.repository import PeriodicMessageRepository


class CreatePeriodicMessageUseCase:
    def __init__(self, repository: PeriodicMessageRepository, mapper: PeriodicMessageMapper):
        self._repository = repository
        self._mapper = mapper

    async def create(self, dto: CreatePeriodicMessageDTO) -> PeriodicMessageDTO:
        created = await self._repository.create(self._mapper.map_create_to_domain(dto))
        return self._mapper.to_dto(created)
