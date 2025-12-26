from typing import Protocol

from core.background_task_runner import BackgroundTaskRunner


class BackgroundJob(Protocol):
    name: str

    def register(self, runner: BackgroundTaskRunner) -> None:
        ...


class BotBackgroundTasks:
    def __init__(self, runner: BackgroundTaskRunner, jobs: list[BackgroundJob]):
        self._runner = runner
        self._jobs = jobs
        self._registered = False

    def start_all(self) -> None:
        if not self._registered:
            for job in self._jobs:
                job.register(self._runner)
            self._registered = True
        self._runner.start_all()

    async def stop_all(self) -> None:
        await self._runner.cancel_all()

