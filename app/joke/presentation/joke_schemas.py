from pydantic import BaseModel, Field


class JokesResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")
