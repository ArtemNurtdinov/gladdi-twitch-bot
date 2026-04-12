import asyncio

from app.task.domain.model.task import Task
from app.task.domain.runner import TaskRunner


class BackgroundTaskRunner(TaskRunner):
    def __init__(self, tasks: list[Task]):
        super().__init__(tasks)
        self._async_tasks: dict[str, asyncio.Task] = {}

    def start_all(self):
        for task in self.registry:
            async_task = asyncio.create_task(task.factory())
            self._async_tasks[task.name] = async_task

    async def cancel_all(self):
        tasks = list(self._async_tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._async_tasks.clear()
