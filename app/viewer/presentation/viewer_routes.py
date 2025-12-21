from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from core.db import get_db
from app.viewer.data.viewer_repository import ViewerRepositoryImpl
from app.viewer.presentation.viewer_schemas import ViewerSessionsResponse, ViewerSessionResponse, ViewerSessionStreamInfo, ViewerSessionWithStreamResponse
from app.viewer.domain.viewer_session_service import ViewerTimeService

router = APIRouter()
viewer_time_service = ViewerTimeService(ViewerRepositoryImpl())


@router.get(
    "/viewers/{channel_name}/{user_name}/sessions",
    response_model=ViewerSessionsResponse,
    summary="Список сессий зрителя",
    description="Получить все сессии просмотра конкретного пользователя на канале",
)
async def get_viewer_sessions(
    channel_name: str,
    user_name: str,
    db: Session = Depends(get_db)
) -> ViewerSessionsResponse:
    try:
        sessions_dto = viewer_time_service.get_user_sessions(db, channel_name, user_name)

        sessions: list[ViewerSessionWithStreamResponse] = []
        for session in sessions_dto:
            if not session.stream:
                raise HTTPException(status_code=404, detail="Стрим не найден для сессии")
            base = ViewerSessionResponse.model_validate(session).model_dump()
            stream_info = ViewerSessionStreamInfo.model_validate(session.stream)
            sessions.append(ViewerSessionWithStreamResponse(**base, stream=stream_info))
        return ViewerSessionsResponse(sessions=sessions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сессий зрителя: {str(e)}")