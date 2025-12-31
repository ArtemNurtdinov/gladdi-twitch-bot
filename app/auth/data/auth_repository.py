from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.auth.data.db.access_token import AccessToken as OrmAccessToken
from app.auth.data.db.user import User as OrmUser
from app.auth.domain.models import (
    AccessToken as DomainAccessToken,
    User as DomainUser,
    UserCreateData,
    UserRole,
    UserUpdateData,
)
from app.auth.domain.repo import AuthRepository


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


def _apply_user_updates(orm_user: OrmUser, updates: UserUpdateData, hashed_password: Optional[str]):
    if updates.email is not None:
        orm_user.email = updates.email
    if updates.first_name is not None:
        orm_user.first_name = updates.first_name
    if updates.last_name is not None:
        orm_user.last_name = updates.last_name
    if updates.role is not None:
        orm_user.role = updates.role
    if updates.is_active is not None:
        orm_user.is_active = updates.is_active
    if hashed_password is not None:
        orm_user.hashed_password = hashed_password
    orm_user.updated_at = datetime.utcnow()


def _to_domain_token(token: OrmAccessToken) -> DomainAccessToken:
    return DomainAccessToken(
        id=token.id,
        user_id=token.user_id,
        token=token.token,
        expires_at=token.expires_at,
        is_active=token.is_active,
        created_at=token.created_at,
    )


class AuthRepositoryImpl(AuthRepository[Session]):
    def get_user_by_email(self, db: Session, email: str) -> Optional[DomainUser]:
        user = db.query(OrmUser).filter(OrmUser.email == email).first()
        return _to_domain_user(user) if user else None

    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[DomainUser]:
        user = db.query(OrmUser).filter(OrmUser.id == user_id).first()
        return _to_domain_user(user) if user else None

    def list_users(self, db: Session, skip: int, limit: int) -> List[DomainUser]:
        users = db.query(OrmUser).offset(skip).limit(limit).all()
        return [_to_domain_user(u) for u in users]

    def create_user(self, db: Session, data: UserCreateData, hashed_password: Optional[str]) -> DomainUser:
        orm_user = OrmUser(
            email=data.email,
            first_name=data.first_name,
            last_name=data.last_name,
            hashed_password=hashed_password,
            role=data.role,
            is_active=data.is_active,
        )
        db.add(orm_user)
        db.flush()
        db.refresh(orm_user)
        return _to_domain_user(orm_user)

    def update_user(self, db: Session, user_id: UUID, updates: UserUpdateData) -> Optional[DomainUser]:
        user = db.query(OrmUser).filter(OrmUser.id == user_id).first()
        if not user:
            return None
        hashed_password = None
        if updates.password:
            hashed_password = updates.password
        _apply_user_updates(user, updates, hashed_password)
        db.flush()
        db.refresh(user)
        return _to_domain_user(user)

    def delete_user(self, db: Session, user_id: UUID) -> bool:
        user = db.query(OrmUser).filter(OrmUser.id == user_id).first()
        if not user:
            return False
        db.delete(user)
        return True

    def create_token(self, db: Session, user_id: UUID, token: str, expires_at: datetime) -> DomainAccessToken:
        orm_token = OrmAccessToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(orm_token)
        db.flush()
        db.refresh(orm_token)
        return _to_domain_token(orm_token)

    def list_tokens(self, db: Session, skip: int, limit: int) -> List[DomainAccessToken]:
        tokens = db.query(OrmAccessToken).offset(skip).limit(limit).all()
        return [_to_domain_token(t) for t in tokens]

    def get_token_by_id(self, db: Session, token_id: UUID) -> Optional[DomainAccessToken]:
        token = db.query(OrmAccessToken).filter(OrmAccessToken.id == token_id).first()
        return _to_domain_token(token) if token else None

    def find_active_token(self, db: Session, token: str, current_time: datetime) -> Optional[DomainAccessToken]:
        record = (
            db.query(OrmAccessToken)
            .filter(
                OrmAccessToken.token == token,
                OrmAccessToken.is_active == True,
                OrmAccessToken.expires_at > current_time,
            )
            .first()
        )
        return _to_domain_token(record) if record else None

    def deactivate_token(self, db: Session, token_id: UUID) -> bool:
        token = db.query(OrmAccessToken).filter(OrmAccessToken.id == token_id).first()
        if not token:
            return False
        token.is_active = False
        return True

    def delete_token(self, db: Session, token_id: UUID) -> bool:
        token = db.query(OrmAccessToken).filter(OrmAccessToken.id == token_id).first()
        if not token:
            return False
        db.delete(token)
        return True
