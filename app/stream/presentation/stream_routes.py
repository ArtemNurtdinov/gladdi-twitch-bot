from dataclasses import asdict

from fastapi import APIRouter, HTTPException, Query

from app.stream.di.container import StreamContainer
from app.stream.presentation.stream_schemas import StreamDetailResponse, StreamListResponse, StreamResponse
from core.db import db_ro_session

router = APIRouter()


@router.get("", summary="Список стримов", response_model=StreamListResponse)
async def get_streams(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(20, ge=1, le=100, description="Количество записей в ответе"),
) -> StreamListResponse:
    try:
        stream_container = StreamContainer()
        with db_ro_session() as session:
            items, total = stream_container.stream_use_case_factory.get(session).get_streams(skip, limit)
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
        stream_details = stream_container.stream_use_case_factory.get(session).get_stream_detail(stream_id)
    if not stream_details:
        raise HTTPException(status_code=404, detail="Стрим не найден")

    payload = {
        **asdict(stream_details.stream),
        "viewer_sessions": [asdict(s) for s in stream_details.sessions],
        "total_watch_minutes": stream_details.total_watch_minutes,
        "total_messages": stream_details.total_messages,
    }
    return StreamDetailResponse(**payload)
