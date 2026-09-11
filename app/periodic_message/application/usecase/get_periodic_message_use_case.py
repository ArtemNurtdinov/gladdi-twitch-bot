from app.periodic_message.application.mapper.periodic_message_mapper import PeriodicMessageMapper
from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.domain.repository import PeriodicMessageRepository


class GetPeriodicMessageUseCase:
    def __init__(self, repository: PeriodicMessageRepository, mapper: PeriodicMessageMapper):
        self._repository = repository
        self._mapper = mapper

    async def get(self, message_id: int) -> PeriodicMessageDTO | None:
        message = await self._repository.get_by_id(message_id)
        if message is None:
            return None
        return self._mapper.to_dto(message)
