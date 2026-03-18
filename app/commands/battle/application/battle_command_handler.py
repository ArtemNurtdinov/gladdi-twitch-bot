from abc import ABC, abstractmethod
from collections.abc import MutableMapping


class BattleCommandHandler(ABC):
    @abstractmethod
    async def handle(self, channel_name: str, display_name: str, battle_waiting_user: MutableMapping[str, str | None]): ...
