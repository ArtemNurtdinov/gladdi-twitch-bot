from datetime import datetime
from typing import Generic, Protocol, TypeVar, Optional, List
from uuid import UUID

from features.auth.domain.models import User, AccessToken, UserCreateData, UserUpdateData

DB = TypeVar("DB")


class AuthRepository(Protocol, Generic[DB]):

    def get_user_by_email(self, db: DB, email: str) -> Optional[User]:
        ...

    def get_user_by_id(self, db: DB, user_id: UUID) -> Optional[User]:
        ...

    def list_users(self, db: DB, skip: int, limit: int) -> List[User]:
        ...

    def create_user(self, db: DB, data: UserCreateData, hashed_password: Optional[str]) -> User:
        ...

    def update_user(self, db: DB, user_id: UUID, updates: UserUpdateData) -> Optional[User]:
        ...

    def delete_user(self, db: DB, user_id: UUID) -> bool:
        ...

    def create_token(self, db: DB, user_id: UUID, token: str, expires_at: datetime) -> AccessToken:
        ...

    def list_tokens(self, db: DB, skip: int, limit: int) -> List[AccessToken]:
        ...

    def get_token_by_id(self, db: DB, token_id: UUID) -> Optional[AccessToken]:
        ...

    def find_active_token(self, db: DB, token: str, current_time: datetime) -> Optional[AccessToken]:
        ...

    def deactivate_token(self, db: DB, token_id: UUID) -> bool:
        ...

    def delete_token(self, db: DB, token_id: UUID) -> bool:
        ...