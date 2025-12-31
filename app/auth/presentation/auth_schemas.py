from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.auth.domain.models import UserRole


class UserResponse(BaseModel):
    id: UUID = Field(..., description="UUID пользователя")
    email: str = Field(..., description="Email пользователя")
    first_name: str | None = Field(..., description="Имя пользователя")
    last_name: str | None = Field(..., description="Фамилия пользователя")
    role: UserRole = Field(..., description="Роль пользователя")
    is_active: bool = Field(..., description="Активен ли пользователь")
    created_at: datetime = Field(..., description="Дата создания")
    updated_at: datetime = Field(..., description="Дата обновления")

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    @field_serializer("created_at", "updated_at")
    def _ser_dt(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        else:
            v = v.astimezone(UTC)
        return v.isoformat().replace("+00:00", "Z")


class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT токен доступа")
    created_at: datetime = Field(..., description="Дата создания токена")
    expires_at: datetime = Field(..., description="Время истечения жизни токена")
    user: UserResponse = Field(..., description="Информация о пользователе")

    @field_serializer("created_at", "expires_at")
    def _ser_dt(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        else:
            v = v.astimezone(UTC)
        return v.isoformat().replace("+00:00", "Z")


class UserCreate(BaseModel):
    email: str
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    role: UserRole
    is_active: bool = True


class UserUpdate(BaseModel):
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    role: UserRole | None = None
    is_active: bool = True
    is_verified: bool | None = None


class TokenResponse(BaseModel):
    id: UUID
    user_id: UUID
    token: str = Field(..., description="JWT токен доступа")
    expires_at: datetime
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("created_at", "expires_at")
    def _ser_dt(self, v: datetime) -> str:
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        else:
            v = v.astimezone(UTC)
        return v.isoformat().replace("+00:00", "Z")


class UserLogin(BaseModel):
    email: str
    password: str
