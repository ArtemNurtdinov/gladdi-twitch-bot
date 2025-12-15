from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from features.stream.stream_schemas import StreamListResponse, StreamResponse
from features.stream.stream_service import StreamService

router = APIRouter()
stream_service = StreamService()


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
) -> StreamListResponse:
    if date_from and date_to and date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from не может быть больше date_to")
    try:
        return stream_service.get_streams(date_from=date_from, date_to=date_to, skip=skip, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения списка стримов: {str(e)}")


@router.get(
    "/streams/{stream_id}",
    response_model=StreamResponse,
    summary="Детали стрима",
    description="Получить детальную информацию о стриме",
)
async def get_stream_detail(stream_id: int) -> StreamResponse:
    stream = stream_service.get_stream_by_id(stream_id)
    if not stream:
        raise HTTPException(status_code=404, detail="Стрим не найден")
    return StreamResponse.model_validate(stream)
