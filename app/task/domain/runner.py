from abc import ABC, abstractmethod

from app.task.domain.model.task import Task


class TaskRunner(ABC):
    def __init__(self, tasks: list[Task]):
        self.registry = tasks

    @abstractmethod
    def start_all(self): ...

    @abstractmethod
    async def cancel_all(self): ...
