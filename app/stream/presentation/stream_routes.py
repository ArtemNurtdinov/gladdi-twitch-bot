from datetime import datetime
from dataclasses import asdict
from fastapi import APIRouter, HTTPException, Query, Depends

from app.stream.bootstrap import get_stream_service_ro
from app.stream.presentation.stream_schemas import StreamListResponse, StreamDetailResponse, StreamResponse
from app.stream.domain.stream_service import StreamService

router = APIRouter()


@router.get(
    "/streams",
    response_model=StreamListResponse,
    summary="Список стримов",
    description="Получить список стримов с пагинацией и фильтром по диапазону дат начала",
)
async def get_streams(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей в ответе"),
    date_from: datetime | None = Query(None, description="Начало диапазона даты начала стрима (UTC)"),
    date_to: datetime | None = Query(None, description="Конец диапазона даты начала стрима (UTC)"),
    stream_service: StreamService = Depends(get_stream_service_ro)
) -> StreamListResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    try:
        items, total = stream_service.get_streams(skip, limit, date_from, date_to)
        return StreamListResponse(
            items=[StreamResponse.model_validate(asdict(item)) for item in items],
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка стримов: {str(e)}")


@router.get(
    "/streams/{stream_id}",
    response_model=StreamDetailResponse,
    summary="Детали стрима",
    description="Получить детальную информацию о стриме",
)
async def get_stream_detail(
    stream_id: int,
    stream_service: StreamService = Depends(get_stream_service_ro)
) -> StreamDetailResponse:
    dto = stream_service.get_stream_detail(stream_id)
    if not dto:
        raise HTTPException(status_code=404, detail="Стрим не найден")

    payload = {
        **asdict(dto.stream),
        "viewer_sessions": [asdict(s) for s in dto.sessions],
    }
    return StreamDetailResponse(**payload)
