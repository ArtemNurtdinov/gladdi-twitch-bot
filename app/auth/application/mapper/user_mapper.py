from app.auth.application.model.user import UserDTO
from app.auth.domain.model.user import User


class UserMapper:
    def map_user_to_dto(self, user: User) -> UserDTO:
        return UserDTO(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
