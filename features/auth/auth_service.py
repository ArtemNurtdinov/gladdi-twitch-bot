import calendar
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from uuid import UUID

import bcrypt
from jose import JWTError, jwt
from jose import exceptions as jose_exceptions
from sqlalchemy.orm import Session

from config import config
from features.auth.domain.models import (
    User,
    AccessToken,
    UserCreateData,
    UserUpdateData,
)
from features.auth.domain.repo import AuthRepository

logger = logging.getLogger(__name__)


class AuthService:
    SECRET_KEY = config.application.auth_secret
    ALGORITHM = config.application.auth_secret_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = config.application.access_token_expire_minutes

    def __init__(self, repo: AuthRepository[Session]):
        self._repo = repo

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

    def generate_access_token(self, user: User) -> str:
        issued_at_utc = datetime.utcnow()
        expires_at_utc = issued_at_utc + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        issued_at_timestamp = calendar.timegm(issued_at_utc.timetuple())
        expires_at_timestamp = calendar.timegm(expires_at_utc.timetuple())

        payload = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "iat": issued_at_timestamp,
            "exp": expires_at_timestamp,
        }

        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    def validate_access_token(self, db: Session, token: str) -> Optional[User]:
        current_time = datetime.utcnow()

        try:
            payload_no_verify = jwt.decode(
                token, self.SECRET_KEY, algorithms=[self.ALGORITHM], options={"verify_exp": False}
            )

            exp_timestamp = payload_no_verify.get("exp", 0)
            current_timestamp_utc = calendar.timegm(current_time.timetuple())
            time_diff_utc = exp_timestamp - current_timestamp_utc

            if time_diff_utc <= 0:
                logger.info(f"ТОКЕН ИСТЕК! Прошло {abs(time_diff_utc)} секунд с момента истечения (по UTC)")
            else:
                logger.info(f"Токен действителен еще {time_diff_utc} секунд ({time_diff_utc / 60:.1f} минут) по UTC")

            if time_diff_utc <= 0:
                raise jose_exceptions.ExpiredSignatureError("Signature has expired")

            payload = jwt.decode(
                token, self.SECRET_KEY, algorithms=[self.ALGORITHM], options={"verify_exp": False}
            )
            user_id = uuid.UUID(payload.get("sub"))

            logger.info("JWT валидация прошла успешно (UTC проверка)")

            access_token = self._repo.find_active_token(db, token, current_time)

            if not access_token:
                logger.info("Токен не найден в БД или неактивен")
                return None

            user = self._repo.get_user_by_id(db, user_id)

            if user and user.is_active:
                logger.info(f"Валидация успешна для пользователя: {user.email}")
                return user

            logger.info("Пользователь не найден или неактивен")
            return None
        except jose_exceptions.ExpiredSignatureError as e:
            logger.info(f"JWT ExpiredSignatureError: {e}")
            return None
        except (JWTError, jose_exceptions.JWTError) as e:
            logger.info(f"JWT InvalidTokenError: {e}")
            return None
        except Exception as e:
            logger.info(f"Unexpected error in validate_access_token: {e}")
            import traceback

            traceback.print_exc()
            return None

    def create_user_from_admin(self, db: Session, user_data: UserCreateData) -> User:
        hashed_password = None
        if user_data.password:
            hashed_password = self.hash_password(user_data.password)

        return self._repo.create_user(db, user_data, hashed_password)

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        return self._repo.get_user_by_email(db, email)

    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[User]:
        return self._repo.get_user_by_id(db, user_id)

    def get_users(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return self._repo.list_users(db, skip, limit)

    def update_user(self, db: Session, user_id: UUID, user_data: UserUpdateData) -> Optional[User]:
        updates = UserUpdateData(
            email=user_data.email,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            role=user_data.role,
            is_active=user_data.is_active,
            password=self.hash_password(user_data.password) if user_data.password else None,
        )
        return self._repo.update_user(db, user_id, updates)

    def delete_user(self, db: Session, user_id: UUID) -> bool:
        return self._repo.delete_user(db, user_id)

    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_token(self, db: Session, user: User) -> AccessToken:
        token_str = self.generate_access_token(user)
        expires_at_utc = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        access_token = self._repo.create_token(db, user.id, token_str, expires_at_utc)

        logger.info(f"Токен сохранен с ID: {access_token.id}")
        return access_token

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_tokens(self, db: Session, skip: int = 0, limit: int = 100) -> List[AccessToken]:
        return self._repo.list_tokens(db, skip, limit)

    def get_token_by_id(self, db: Session, token_id: UUID) -> Optional[AccessToken]:
        return self._repo.get_token_by_id(db, token_id)

    def deactivate_token(self, db: Session, token_id: UUID) -> bool:
        return self._repo.deactivate_token(db, token_id)

    def delete_token(self, db: Session, token_id: UUID) -> bool:
        return self._repo.delete_token(db, token_id)

