from fastapi import APIRouter, HTTPException, Depends

from app.viewer.bootstrap import get_viewer_service_ro
from app.viewer.presentation.viewer_schemas import ViewerSessionsResponse, ViewerSessionResponse, ViewerSessionStreamInfo, ViewerSessionWithStreamResponse
from app.viewer.domain.viewer_session_service import ViewerTimeService

router = APIRouter()


@router.get(
    "/viewers/{channel_name}/{user_name}/sessions",
    response_model=ViewerSessionsResponse,
    summary="Список сессий зрителя",
    description="Получить все сессии просмотра конкретного пользователя на канале",
)
async def get_viewer_sessions(
    channel_name: str,
    user_name: str,
    viewer_service: ViewerTimeService = Depends(get_viewer_service_ro)
) -> ViewerSessionsResponse:
    try:
        sessions_dto = viewer_service.get_user_sessions(channel_name, user_name)

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