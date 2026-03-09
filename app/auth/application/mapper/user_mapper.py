from app.auth.application.dto import UserDto
from app.auth.domain.model.user import User


class UserMapper:
    def map_user_to_dto(self, user: User) -> UserDto:
        return UserDto(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
