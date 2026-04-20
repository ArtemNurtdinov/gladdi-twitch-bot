from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.auth.domain.model.access_token import AccessToken
from app.auth.domain.model.user import User
from app.auth.domain.models import UserCreateData


class AuthRepository(ABC):
    @abstractmethod
    def get_user_by_email(self, email: str) -> User | None: ...

    @abstractmethod
    def get_user_by_id(self, user_id: UUID) -> User | None: ...

    @abstractmethod
    def create_user(self, data: UserCreateData, hashed_password: str) -> User: ...

    @abstractmethod
    def create_token(self, user_id: UUID, token: str, expires_at: datetime) -> AccessToken: ...

    @abstractmethod
    def find_active_token(self, token: str, current_time: datetime) -> AccessToken | None: ...
