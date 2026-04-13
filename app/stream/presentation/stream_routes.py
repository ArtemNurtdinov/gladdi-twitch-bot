from dataclasses import asdict
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from app.stream.di.container import StreamContainer
from app.stream.presentation.stream_schemas import StreamDetailResponse, StreamListResponse, StreamResponse
from core.db import db_ro_session

router = APIRouter()


@router.get("", summary="Список стримов", response_model=StreamListResponse)
async def get_streams(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей в ответе"),
    date_from: datetime | None = Query(None, description="Начало диапазона даты начала стрима (UTC)"),
    date_to: datetime | None = Query(None, description="Конец диапазона даты начала стрима (UTC)"),
) -> StreamListResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    try:
        stream_container = StreamContainer()
        with db_ro_session() as session:
            items, total = stream_container.stream_use_case(session).get_streams(skip, limit, date_from, date_to)
        return StreamListResponse(
            items=[StreamResponse.model_validate(asdict(item)) for item in items],
            total=total,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка стримов: {str(e)}")


@router.get("/{stream_id}", summary="Детали стрима", response_model=StreamDetailResponse)
async def get_stream_detail(
    stream_id: int,
) -> StreamDetailResponse:
    stream_container = StreamContainer()
    with db_ro_session() as session:
        stream_details = stream_container.stream_use_case(session).get_stream_detail(stream_id)
    if not stream_details:
        raise HTTPException(status_code=404, detail="Стрим не найден")

    payload = {
        **asdict(stream_details.stream),
        "viewer_sessions": [asdict(s) for s in stream_details.sessions],
        "total_watch_minutes": stream_details.total_watch_minutes,
        "total_messages": stream_details.total_messages,
    }
    return StreamDetailResponse(**payload)
