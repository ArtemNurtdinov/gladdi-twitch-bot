from fastapi import APIRouter, Depends, HTTPException, Query

from app.common.infrastructure.db.db import db_ro_session, db_rw_session
from app.core.network.api.model.base_response import BaseResponse
from app.periodic_message.di.container import PeriodicMessageContainer
from app.periodic_message.presentation.api.model.periodic_message_schema import PeriodicMessageSchema
from app.periodic_message.presentation.api.model.request.create_periodic_message_request import CreatePeriodicMessageRequest
from app.periodic_message.presentation.api.model.request.patch_periodic_message_request import PatchPeriodicMessageRequest
from app.periodic_message.presentation.api.model.response.all_periodic_messages_response import AllPeriodicMessagesResponse
from app.periodic_message.presentation.api.model.response.create_periodic_message_response import CreatePeriodicMessageResponse
from app.periodic_message.presentation.deps import get_periodic_message_container

router = APIRouter()


@router.get("", summary="Получение всех периодических сообщений", response_model=AllPeriodicMessagesResponse)
async def get_all_periodic_messages(
    channel_name: str = Query(..., description="Имя канала"),
    container: PeriodicMessageContainer = Depends(get_periodic_message_container),
) -> AllPeriodicMessagesResponse:
    with db_ro_session() as session:
        messages = await container.get_all_use_case(session).get_all(channel_name)
    items = [container.schema_mapper.map_to_schema(message) for message in messages]
    return AllPeriodicMessagesResponse(periodic_messages=items)


@router.post("", summary="Создание периодического сообщения", response_model=CreatePeriodicMessageResponse)
async def create_periodic_message(
    body: CreatePeriodicMessageRequest,
    container: PeriodicMessageContainer = Depends(get_periodic_message_container),
) -> CreatePeriodicMessageResponse:
    dto = container.schema_mapper.map_create_to_dto(body)
    with db_rw_session() as session:
        created = await container.create_use_case(session).create(dto)
    return CreatePeriodicMessageResponse(periodic_message=container.schema_mapper.map_to_schema(created))


@router.get("/{message_id}", summary="Получить периодическое сообщение по ID", response_model=PeriodicMessageSchema)
async def get_periodic_message(
    message_id: int,
    container: PeriodicMessageContainer = Depends(get_periodic_message_container),
) -> PeriodicMessageSchema:
    with db_ro_session() as session:
        message = await container.get_use_case(session).get(message_id)
    if message is None:
        raise HTTPException(status_code=404, detail="Периодическое сообщение не найдено")
    return container.schema_mapper.map_to_schema(message)


@router.patch("/{message_id}", summary="Отредактировать периодическое сообщение", response_model=CreatePeriodicMessageResponse)
async def patch_periodic_message(
    message_id: int,
    body: PatchPeriodicMessageRequest,
    container: PeriodicMessageContainer = Depends(get_periodic_message_container),
) -> CreatePeriodicMessageResponse:
    if body.id != message_id:
        raise HTTPException(status_code=400, detail="ID в пути и теле запроса не совпадают")

    dto = container.schema_mapper.map_patch_to_dto(body)
    with db_rw_session() as session:
        updated = await container.patch_use_case(session).patch(dto)

    if updated is None:
        raise HTTPException(status_code=404, detail="Периодическое сообщение не найдено")

    return CreatePeriodicMessageResponse(periodic_message=container.schema_mapper.map_to_schema(updated))


@router.delete("/{message_id}", summary="Удаление периодического сообщения", response_model=BaseResponse)
async def delete_periodic_message(
    message_id: int,
    container: PeriodicMessageContainer = Depends(get_periodic_message_container),
) -> BaseResponse:
    with db_rw_session() as session:
        await container.delete_use_case(session).execute(message_id)
    return BaseResponse(message="Периодическое сообщение успешно удалено")
