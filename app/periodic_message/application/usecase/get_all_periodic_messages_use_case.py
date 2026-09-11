from app.periodic_message.application.mapper.periodic_message_mapper import PeriodicMessageMapper
from app.periodic_message.application.model.periodic_message import PeriodicMessageDTO
from app.periodic_message.domain.repository import PeriodicMessageRepository


class GetAllPeriodicMessagesUseCase:
    def __init__(self, repository: PeriodicMessageRepository, mapper: PeriodicMessageMapper):
        self._repository = repository
        self._mapper = mapper

    async def get_all(self, channel_name: str) -> list[PeriodicMessageDTO]:
        messages = self._repository.get_all_by_channel(channel_name)
        return [self._mapper.to_dto(message) for message in messages]
