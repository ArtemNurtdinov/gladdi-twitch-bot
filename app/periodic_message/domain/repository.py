from abc import ABC, abstractmethod
from datetime import datetime

from app.periodic_message.domain.model.periodic_message import PeriodicMessage, PeriodicMessageCreate, PeriodicMessagePatch


class PeriodicMessageRepository(ABC):
    @abstractmethod
    def get_all_by_channel(self, channel_name: str) -> list[PeriodicMessage]: ...

    @abstractmethod
    async def get_by_id(self, message_id: int) -> PeriodicMessage | None: ...

    @abstractmethod
    async def create(self, message: PeriodicMessageCreate) -> PeriodicMessage: ...

    @abstractmethod
    async def patch(self, message: PeriodicMessagePatch) -> PeriodicMessage | None: ...

    @abstractmethod
    async def delete(self, message_id: int) -> None: ...

    @abstractmethod
    def get_due_enabled(self, channel_name: str, now: datetime) -> list[PeriodicMessage]: ...

    @abstractmethod
    async def update_schedule(self, message_id: int, last_sent_at: datetime, next_send_at: datetime) -> None: ...
