import asyncio

from app.task.domain.job import BackgroundJob


class BackgroundTaskRunner:
    def __init__(self, jobs: list[BackgroundJob]):
        self.registry = jobs
        self._async_tasks: dict[str, asyncio.Task] = {}

    def start_all(self, channel_name: str, bot_name: str):
        for job in self.registry:
            job.apply_channel(channel_name, bot_name)
            async_task = asyncio.create_task(job.run())
            self._async_tasks[job.name] = async_task

    async def cancel_all(self):
        tasks = list(self._async_tasks.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        self._async_tasks.clear()
