from app.periodic_message.domain.repository import PeriodicMessageRepository


class DeletePeriodicMessageUseCase:
    def __init__(self, repository: PeriodicMessageRepository):
        self._repository = repository

    async def execute(self, message_id: int) -> None:
        await self._repository.delete(message_id)
