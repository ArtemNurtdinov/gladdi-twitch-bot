from fastapi import Depends

from app.bootstrap.app_container import AppContainer
from app.presentation.deps import get_app
from app.stream.di.container import StreamContainer


def get_stream_container(app: AppContainer = Depends(get_app)) -> StreamContainer:
    return app.stream
