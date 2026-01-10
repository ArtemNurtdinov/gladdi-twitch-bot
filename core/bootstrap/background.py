from dataclasses import dataclass

from core.background.task_runner import BackgroundTaskRunner


@dataclass
class BackgroundProviders:
    runner: BackgroundTaskRunner


def build_background_providers() -> BackgroundProviders:
    return BackgroundProviders(runner=BackgroundTaskRunner())
