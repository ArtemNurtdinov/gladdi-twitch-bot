from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.data.auth_repository import AuthRepositoryImpl
from app.auth.domain.auth_service import AuthService
from app.auth.domain.models import User, UserRole
from bootstrap.config_provider import get_config
from core.config import Config
from core.db import get_db

security = HTTPBearer()
security_optional = HTTPBearer(auto_error=False)


def get_auth_service(config: Config = Depends(get_config)) -> AuthService:
    auth_repo = AuthRepositoryImpl()
    return AuthService(
        auth_secret=config.application.auth_secret,
        auth_secret_algorithm=config.application.auth_secret_algorithm,
        access_token_expires_minutes=config.application.access_token_expire_minutes,
        repo=auth_repo,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> User:
    user = auth_service.validate_access_token(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user


def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Недостаточно прав доступа")
    return current_user


def get_optional_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security_optional),
    auth_service: AuthService = Depends(get_auth_service),
    db: Session = Depends(get_db),
) -> User | None:
    if credentials is None:
        return None
    user = auth_service.validate_access_token(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Недействительный токен", headers={"WWW-Authenticate": "Bearer"})
    return user
