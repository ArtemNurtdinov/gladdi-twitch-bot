from app.task.domain.job import BackgroundJob
from app.task.domain.runner import TaskRunner


class BackgroundTasks:
    def __init__(self, runner: TaskRunner, jobs: list[BackgroundJob]):
        self._runner = runner
        self._jobs = jobs

    def start_all(self) -> None:
        for job in self._jobs:
            self._runner.register(job.name, job.run)
        self._runner.start_all()

    async def stop_all(self) -> None:
        await self._runner.cancel_all()
