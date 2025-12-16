from fastapi import APIRouter, HTTPException

from features.viewer.viewer_schemas import ViewerSessionsResponse, ViewerSessionResponse, ViewerSessionStreamInfo, ViewerSessionWithStreamResponse
from features.viewer.viewer_session_service import ViewerTimeService

router = APIRouter()
viewer_time_service = ViewerTimeService()


@router.get(
    "/viewers/{channel_name}/{user_name}/sessions",
    response_model=ViewerSessionsResponse,
    summary="Список сессий зрителя",
    description="Получить все сессии просмотра конкретного пользователя на канале",
)
async def get_viewer_sessions(
    channel_name: str,
    user_name: str
) -> ViewerSessionsResponse:
    try:
        sessions_db = viewer_time_service.get_user_sessions(channel_name, user_name)

        sessions: list[ViewerSessionWithStreamResponse] = []
        for session in sessions_db:
            base = ViewerSessionResponse.model_validate(session).model_dump()
            stream_info = ViewerSessionStreamInfo.model_validate(session.stream)
            sessions.append(ViewerSessionWithStreamResponse(**base, stream=stream_info))
        return ViewerSessionsResponse(sessions=sessions)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения сессий зрителя: {str(e)}")