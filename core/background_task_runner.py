import asyncio
from typing import Callable, Awaitable, Dict


class BackgroundTaskRunner:

    def __init__(self):
        self._registry: list[tuple[str, Callable[[], Awaitable[None]]]] = []
        self._tasks: Dict[str, asyncio.Task] = {}

    def register(self, name: str, coro_factory: Callable[[], Awaitable[None]]):
        self._registry.append((name, coro_factory))

    def start_all(self):
        for name, factory in self._registry:
            if name in self._tasks and not self._tasks[name].done():
                continue

            task = asyncio.create_task(factory())
            self._tasks[name] = task

            def _cleanup(_task: asyncio.Task, _name=name):
                self._tasks.pop(_name, None)

            task.add_done_callback(_cleanup)

    async def cancel_all(self):
        tasks = list(self._tasks.values())
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

