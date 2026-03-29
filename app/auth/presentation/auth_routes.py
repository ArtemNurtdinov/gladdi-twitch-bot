from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.application.contracts import LoginResponse, UserLogin, UserResponse
from app.auth.application.model.user import UserDTO
from app.auth.application.usecase.login_use_case import LoginUseCase
from app.auth.application.usecase.validate_access_token_use_case import ValidateAccessTokenUseCase
from app.auth.di.dependencies import provide_login_use_case, provide_validate_access_token_use_case
from app.auth.domain.model.role import UserRole

router = APIRouter()
admin_router = APIRouter()
security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(provide_validate_access_token_use_case),
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
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(provide_validate_access_token_use_case),
) -> UserDTO | None:
    if credentials is None:
        return None
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(provide_validate_access_token_use_case),
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
    validate_access_token_use_case: ValidateAccessTokenUseCase = Depends(provide_validate_access_token_use_case),
) -> UserDTO | None:
    if credentials is None:
        return None
    user = validate_access_token_use_case.validate_access_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: UserDTO = Depends(get_current_user)):
    return UserResponse.model_validate(current_user).model_dump()


@router.post("/login", response_model=LoginResponse)
async def login(user_data: UserLogin, login_use_case: LoginUseCase = Depends(provide_login_use_case)):
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
