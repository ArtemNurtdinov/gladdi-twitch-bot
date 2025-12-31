from dataclasses import dataclass

from core.background_task_runner import BackgroundTaskRunner


@dataclass
class BackgroundProviders:
    background_runner: BackgroundTaskRunner


def build_background_providers() -> BackgroundProviders:
    return BackgroundProviders(background_runner=BackgroundTaskRunner())

