from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.joke.di.container import JokeContainer
from app.presentation.deps import get_app


def get_joke_container(app: AppContainer = Depends(get_app)) -> JokeContainer:
    return app.joke
