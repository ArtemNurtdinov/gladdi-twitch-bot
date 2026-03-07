from fastapi import APIRouter, Depends

from app.ai.gen.prompt.application.get_system_prompt_use_case import GetSystemPromptUseCase
from app.ai.gen.prompt.application.update_system_prompt_use_case import UpdateSystemPromptUseCase
from app.ai.gen.prompt.deps import get_get_system_prompt_use_case, get_update_system_prompt_use_case
from app.ai.gen.prompt.presentation.system_prompt_schemas import SystemPromptResponse, SystemPromptUpdate
from app.auth.application.model.user import UserDTO
from bootstrap.auth_provider import get_admin_user

admin_router = APIRouter()


@admin_router.get("/system-prompt/{channel_name}", response_model=SystemPromptResponse, summary="Получить системный промпт канала")
async def get_system_prompt(
    channel_name: str,
    current_user: UserDTO = Depends(get_admin_user),
    use_case: GetSystemPromptUseCase = Depends(get_get_system_prompt_use_case),
):
    system_prompt = use_case.handle(channel_name)
    return SystemPromptResponse(channel_name=channel_name, content=system_prompt.prompt)


@admin_router.put("/system-prompt/{channel_name}", response_model=SystemPromptResponse, summary="Обновить системный промпт канала")
async def update_system_prompt(
    channel_name: str,
    body: SystemPromptUpdate,
    current_user: UserDTO = Depends(get_admin_user),
    use_case: UpdateSystemPromptUseCase = Depends(get_update_system_prompt_use_case),
):
    use_case.update_system_prompt(channel_name, body.content)
    return SystemPromptResponse(channel_name=channel_name, content=body.content)
