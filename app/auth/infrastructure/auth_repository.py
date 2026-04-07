from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.domain.auth_repository import AuthRepository
from app.auth.domain.model.access_token import (
    AccessToken as DomainAccessToken,
)
from app.auth.domain.model.role import UserRole
from app.auth.domain.model.user import (
    User as DomainUser,
)
from app.auth.domain.models import (
    UserCreateData,
)
from app.auth.infrastructure.db.access_token import AccessToken as OrmAccessToken
from app.auth.infrastructure.db.user import User as OrmUser
from app.stream.infrastructure.mappers.stream_mapper import normalize_datetime


def _to_domain_user(orm_user: OrmUser) -> DomainUser:
    return DomainUser(
        id=orm_user.id,
        email=orm_user.email,
        first_name=orm_user.first_name,
        last_name=orm_user.last_name,
        role=UserRole(orm_user.role.value),
        is_active=orm_user.is_active,
        hashed_password=orm_user.hashed_password,
        created_at=orm_user.created_at,
        updated_at=orm_user.updated_at,
    )


def _to_domain_token(token: OrmAccessToken) -> DomainAccessToken:
    return DomainAccessToken(
        id=token.id,
        user_id=token.user_id,
        token=token.token,
        expires_at=normalize_datetime(token.expires_at),
        is_active=token.is_active,
        created_at=normalize_datetime(token.created_at),
    )


class AuthRepositoryImpl(AuthRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_user_by_email(self, email: str) -> DomainUser | None:
        stmt = select(OrmUser).where(OrmUser.email == email)
        user = self._db.execute(stmt).scalars().first()
        return _to_domain_user(user) if user else None

    def get_user_by_id(self, user_id: UUID) -> DomainUser | None:
        stmt = select(OrmUser).where(OrmUser.id == user_id)
        user = self._db.execute(stmt).scalars().first()
        return _to_domain_user(user) if user else None

    def create_user(self, data: UserCreateData, hashed_password: str) -> DomainUser:
        orm_user = OrmUser(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            hashed_password=hashed_password,
            role=data.role,
            is_active=data.is_active,
        )
        self._db.add(orm_user)
        self._db.flush()
        self._db.refresh(orm_user)
        return _to_domain_user(orm_user)

    def create_token(self, user_id: UUID, token: str, expires_at: datetime) -> DomainAccessToken:
        expires_at_naive = expires_at.replace(tzinfo=None)
        orm_token = OrmAccessToken(user_id=user_id, token=token, expires_at=expires_at_naive)
        self._db.add(orm_token)
        self._db.flush()
        self._db.refresh(orm_token)
        return _to_domain_token(orm_token)

    def find_active_token(self, token: str, current_time: datetime) -> DomainAccessToken | None:
        stmt = select(OrmAccessToken).where(OrmAccessToken.token == token).where(OrmAccessToken.is_active)
        record = self._db.execute(stmt).scalars().first()
        return _to_domain_token(record) if record else None
