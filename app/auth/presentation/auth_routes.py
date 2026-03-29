from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.application.auth_service import AuthService
from app.auth.application.contracts import LoginResponse, TokenResponse, UserCreate, UserLogin, UserResponse, UserUpdate
from app.auth.application.dto import UserCreateDto, UserUpdateDto
from app.auth.application.model.user import UserDTO
from app.auth.application.usecase.create_user_from_admin_use_case import CreateUserFromAdminUseCase
from app.auth.application.usecase.get_user_by_email_use_case import GetUserByEmailUseCase
from app.auth.application.usecase.get_user_by_id_use_case import GetUserByIdUseCase
from app.auth.application.usecase.get_users_use_case import GetUsersUseCase
from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.domain.model.role import UserRole
from app.bootstrap import (
    get_auth_service,
    get_create_user_from_admin_use_case,
    get_login_use_case,
    get_user_by_email_use_case,
    get_user_by_id_use_case,
    get_users_use_case,
    get_validate_access_token_use_case,
)

router = APIRouter()
admin_router = APIRouter()
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(get_validate_access_token_use_case),
) -> UserDTO:
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_admin_user(current_user: UserDTO = Depends(get_current_user)) -> UserDTO:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа")
    return current_user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(get_validate_access_token_use_case),
) -> UserDTO | None:
    if credentials is None:
        return None
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


@admin_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: UserDTO = Depends(get_admin_user),
    user_by_email_use_case: GetUserByEmailUseCase = Depends(get_user_by_email_use_case),
    create_user_from_admin_use_case: CreateUserFromAdminUseCase = Depends(get_create_user_from_admin_use_case),
):
    existing_user = user_by_email_use_case.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует")

    if not user_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль обязателен")

    app_input = UserCreateDto(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password=user_data.password,
        role=user_data.role,
        is_active=user_data.is_active,
    )
    user = create_user_from_admin_use_case.create_user(app_input)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDTO = Depends(get_current_user)):
    return UserResponse.model_validate(current_user).model_dump()


@admin_router.get("/users", response_model=list[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDTO = Depends(get_admin_user),
    users_use_case: GetUsersUseCase = Depends(get_users_use_case),
):
    users = users_use_case.get_users(skip, limit)
    return [UserResponse.model_validate(user) for user in users]


@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: UserDTO = Depends(get_admin_user),
    user_by_id_use_case: GetUserByIdUseCase = Depends(get_user_by_id_use_case),
):
    user = user_by_id_use_case.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@admin_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
    user_by_email_use_case: GetUserByEmailUseCase = Depends(get_user_by_email_use_case),
):
    if user_data.email:
        existing_user = user_by_email_use_case.get_user_by_email(user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует")

    app_update = UserUpdateDto(
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password=user_data.password,
        role=user_data.role,
        is_active=user_data.is_active,
    )
    user = auth_service.update_user(user_id, app_update)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")

    success = auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")

    return {"message": "Пользователь удален"}


@admin_router.get("/tokens", response_model=list[TokenResponse])
async def get_tokens(
    skip: int = 0,
    limit: int = 100,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    tokens = auth_service.get_tokens(skip, limit)
    return [TokenResponse.model_validate(token) for token in tokens]


@admin_router.get("/tokens/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: UUID,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    token = auth_service.get_token_by_id(token_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return TokenResponse.model_validate(token)


@admin_router.patch("/tokens/{token_id}/deactivate")
async def deactivate_token(
    token_id: UUID,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    success = auth_service.deactivate_token(token_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return {"message": "Токен деактивирован"}


@admin_router.delete("/tokens/{token_id}")
async def delete_token(
    token_id: UUID,
    current_user: UserDTO = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    success = auth_service.delete_token(token_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return {"message": "Токен удален"}


@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, login_use_case: LoginUseCase = Depends(get_login_use_case)):
    result = login_use_case.login(user_data.email, user_data.password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"}
        )
    user_response = UserResponse.model_validate(result.user)
    return LoginResponse(
        access_token=result.access_token,
        created_at=result.created_at,
        expires_at=result.expires_at,
        user=user_response,
    )
