from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from uuid import UUID

from features.auth.auth_schemas import UserResponse, UserCreate, UserUpdate, TokenResponse, UserLogin, LoginResponse
from features.auth.auth_service import AuthService
from features.auth.dependencies import get_current_user, get_auth_service, get_admin_user
from features.auth.db.user import User

router = APIRouter(prefix="/auth")
admin_router = APIRouter(prefix="/admin")
security = HTTPBearer()


@admin_router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    existing_user = auth_service.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует")

    if not user_data.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пароль обязателен")

    user = auth_service.create_user_from_admin(user_data)
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user)
):
    return UserResponse.model_validate(current_user).model_dump()


@admin_router.get("/users", response_model=List[UserResponse])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    users = auth_service.get_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(user) for user in users]


@admin_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@admin_router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    if user_data.email:
        existing_user = auth_service.get_user_by_email(user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Пользователь с таким email уже существует")

    user = auth_service.update_user(user_id, user_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return UserResponse.model_validate(user)


@admin_router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Нельзя удалить самого себя")

    success = auth_service.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Пользователь не найден")
    return {"message": "Пользователь удален"}


@admin_router.get("/tokens", response_model=List[TokenResponse])
async def get_tokens(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    tokens = auth_service.get_tokens(skip=skip, limit=limit)
    return [TokenResponse.model_validate(token) for token in tokens]


@admin_router.get("/tokens/{token_id}", response_model=TokenResponse)
async def get_token(
    token_id: UUID,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    token = auth_service.get_token_by_id(token_id)
    if not token:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return TokenResponse.model_validate(token)


@admin_router.patch("/tokens/{token_id}/deactivate")
async def deactivate_token(
    token_id: UUID,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    success = auth_service.deactivate_token(token_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return {"message": "Токен деактивирован"}


@admin_router.delete("/tokens/{token_id}")
async def delete_token(
    token_id: UUID,
    current_user: User = Depends(get_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    success = auth_service.delete_token(token_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Токен не найден")
    return {"message": "Токен удален"}


@router.post("/login", response_model=LoginResponse)
async def login(
    user_data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    user = auth_service.authenticate_user(user_data.email, user_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный email или пароль", headers={"WWW-Authenticate": "Bearer"})

    access_token = auth_service.create_token(user)
    user_response = UserResponse.model_validate(user)

    return LoginResponse(access_token=access_token.token, created_at=access_token.created_at, expires_at=access_token.expires_at, user=user_response)
