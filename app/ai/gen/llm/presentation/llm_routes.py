from fastapi import APIRouter, Depends, HTTPException, Request

from app.ai.gen.di.container import AIContainer
from app.ai.gen.llm.domain.model.assistant import AIAssistant
from app.ai.gen.llm.presentation.model.assistant_response import AssistantResponse, AssistantUpdate
from app.core.network.api.model.base_response import BaseResponse
from core.db import db_ro_session

router = APIRouter()


def get_ai_container(request: Request) -> AIContainer:
    return request.app.state.ai_container


@router.get("/assistant/{channel_name}", response_model=AssistantResponse)
async def get_assistant(
    channel_name: str,
    ai_container: AIContainer = Depends(get_ai_container),
):
    with db_ro_session() as session:
        assistant = await ai_container.get_assistant_use_case_provider.get(session).get_assistant(channel_name)
    return AssistantResponse(channel_name=channel_name, assistant=assistant.value)


@router.put("/assistant/{channel_name}", response_model=BaseResponse)
async def save_assistant(
    channel_name: str,
    body: AssistantUpdate,
    ai_container: AIContainer = Depends(get_ai_container),
):
    try:
        assistant = AIAssistant(body.assistant)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Неизвестный ассистент: {body.assistant}. Доступные: {[a.value for a in AIAssistant]}",
        )

    with db_ro_session() as session:
        await ai_container.save_assistant_use_case_provider.get(session).save_assistant(channel_name, assistant)

    return BaseResponse(message="Ассистент успешно сохранён")
