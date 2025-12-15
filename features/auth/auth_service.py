import logging
import uuid
from typing import Optional, List, Dict, Any
from config import config
import bcrypt
from datetime import datetime, timedelta
from sqlalchemy import and_
from db.base import SessionLocal
from features.auth.auth_schemas import UserCreate, UserUpdate
from features.auth.db.access_token import AccessToken
from features.auth.db.user import User
import calendar
from jose import JWTError, jwt
from jose import exceptions as jose_exceptions

logger = logging.getLogger(__name__)


class AuthService:
    SECRET_KEY = config.application.auth_secret
    ALGORITHM = config.application.auth_secret_algorithm
    ACCESS_TOKEN_EXPIRE_MINUTES = config.application.access_token_expire_minutes

    def hash_password(self, password: str) -> str:
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

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
            "exp": expires_at_timestamp
        }

        token = jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    def validate_access_token(self, token: str) -> Optional[User]:
        db = SessionLocal()

        current_time = datetime.utcnow()

        try:
            payload_no_verify = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM], options={"verify_exp": False})

            exp_timestamp = payload_no_verify.get('exp', 0)
            current_timestamp_utc = calendar.timegm(current_time.timetuple())
            time_diff_utc = exp_timestamp - current_timestamp_utc

            if time_diff_utc <= 0:
                logger.info(f"ТОКЕН ИСТЕК! Прошло {abs(time_diff_utc)} секунд с момента истечения (по UTC)")
            else:
                logger.info(f"Токен действителен еще {time_diff_utc} секунд ({time_diff_utc / 60:.1f} минут) по UTC")

            if time_diff_utc <= 0:
                raise jose_exceptions.ExpiredSignatureError("Signature has expired")

            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM], options={"verify_exp": False})
            user_id = uuid.UUID(payload.get("sub"))

            logger.info(f"JWT валидация прошла успешно (UTC проверка)")

            access_token = db.query(AccessToken).filter(and_(AccessToken.token == token, AccessToken.is_active == True, AccessToken.expires_at > current_time)).first()

            if not access_token:
                logger.info(f"Токен не найден в БД или неактивен")
                return None

            user = db.query(User).filter(and_(User.id == user_id, User.is_active == True)).first()

            if user:
                logger.info(f"Валидация успешна для пользователя: {user.email}")
            else:
                logger.info(f"Пользователь не найден или неактивен")

            return user

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
        finally:
            db.close()

    def create_user_from_admin(self, user_data: UserCreate) -> User:
        db = SessionLocal()
        try:
            hashed_password = None
            if user_data.password:
                hashed_password = self.hash_password(user_data.password)

            db_user = User(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                hashed_password=hashed_password,
                role=user_data.role,
                is_active=user_data.is_active
            )
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            return db_user
        finally:
            db.close()

    def get_user_by_email(self, email: str) -> Optional[User]:
        db = SessionLocal()
        try:
            return db.query(User).filter(User.email == email).first()
        finally:
            db.close()

    def get_user_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        db = SessionLocal()
        try:
            return db.query(User).filter(User.id == user_id).first()
        finally:
            db.close()

    def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        db = SessionLocal()
        try:
            return db.query(User).offset(skip).limit(limit).all()
        finally:
            db.close()

    def update_user(self, user_id: uuid.UUID, user_data: UserUpdate) -> Optional[User]:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None

            update_data = user_data.dict(exclude_unset=True)
            if 'password' in update_data and update_data['password']:
                update_data['hashed_password'] = self.hash_password(update_data.pop('password'))

            for field, value in update_data.items():
                setattr(user, field, value)

            user.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(user)
            return user
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {user_id}: {e}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            db.close()

    def delete_user(self, user_id: uuid.UUID) -> bool:
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return False

            db.delete(user)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        user = self.get_user_by_email(email)
        if not user:
            return None
        if not user.hashed_password or not self.verify_password(password, user.hashed_password):
            return None
        if not user.is_active:
            return None
        return user

    def create_token(self, user: User) -> AccessToken:
        db = SessionLocal()
        try:
            token_str = self.generate_access_token(user)
            expires_at_utc = datetime.utcnow() + timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

            access_token = AccessToken(user_id=user.id, token=token_str, expires_at=expires_at_utc)
            db.add(access_token)
            db.commit()
            db.refresh(access_token)

            logger.info(f"Токен сохранен с ID: {access_token.id}")
            return access_token
        except Exception as e:
            db.rollback()
            logger.info(f"Error creating token for user {user.id}: {e}")
            raise e
        finally:
            db.close()

    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload
        except JWTError:
            return None

    def get_tokens(self, skip: int = 0, limit: int = 100) -> List[AccessToken]:
        db = SessionLocal()
        try:
            return db.query(AccessToken).offset(skip).limit(limit).all()
        finally:
            db.close()

    def get_token_by_id(self, token_id: uuid.UUID) -> Optional[AccessToken]:
        db = SessionLocal()
        try:
            return db.query(AccessToken).filter(AccessToken.id == token_id).first()
        finally:
            db.close()

    def deactivate_token(self, token_id: uuid.UUID) -> bool:
        db = SessionLocal()
        try:
            token = db.query(AccessToken).filter(AccessToken.id == token_id).first()
            if not token:
                return False

            token.is_active = False
            db.commit()
            return True
        finally:
            db.close()

    def delete_token(self, token_id: uuid.UUID) -> bool:
        db = SessionLocal()
        try:
            token = db.query(AccessToken).filter(AccessToken.id == token_id).first()
            if not token:
                return False

            db.delete(token)
            db.commit()
            return True
        finally:
            db.close()

    def get_all_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        db = SessionLocal()
        try:
            return db.query(User).offset(skip).limit(limit).all()
        finally:
            db.close()
