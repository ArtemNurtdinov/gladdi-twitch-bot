from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.stream.application.stream_query_use_case import StreamQueryUseCase
from app.stream.presentation.stream_schemas import StreamDetailResponse, StreamListResponse, StreamResponse
from bootstrap.stream_provider import get_stream_query_use_case_ro

router = APIRouter()


@router.get(
    "",
    response_model=StreamListResponse,
    summary="Список стримов",
    description="Получить список стримов с пагинацией и фильтром по диапазону дат начала",
)
async def get_streams(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей в ответе"),
    date_from: datetime | None = Query(None, description="Начало диапазона даты начала стрима (UTC)"),
    date_to: datetime | None = Query(None, description="Конец диапазона даты начала стрима (UTC)"),
    stream_query_use_case: StreamQueryUseCase = Depends(get_stream_query_use_case_ro),
) -> StreamListResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    try:
        items, total = stream_query_use_case.get_streams(skip, limit, date_from, date_to)
        return StreamListResponse(
            items=[StreamResponse.model_validate(asdict(item)) for item in items],
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка стримов: {str(e)}")


@router.get(
    "/{stream_id}",
    response_model=StreamDetailResponse,
    summary="Детали стрима",
    description="Получить детальную информацию о стриме",
)
async def get_stream_detail(
    stream_id: int, stream_query_use_case: StreamQueryUseCase = Depends(get_stream_query_use_case_ro)
) -> StreamDetailResponse:
    dto = stream_query_use_case.get_stream_detail(stream_id)
    if not dto:
        raise HTTPException(status_code=404, detail="Стрим не найден")

    payload = {
        **asdict(dto.stream),
        "viewer_sessions": [asdict(s) for s in dto.sessions],
        "total_watch_minutes": dto.total_watch_minutes,
        "total_messages": dto.total_messages,
    }
    return StreamDetailResponse(**payload)
