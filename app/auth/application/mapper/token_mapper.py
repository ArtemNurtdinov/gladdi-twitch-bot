from app.auth.application.dto import TokenDto
from app.auth.domain.model.access_token import AccessToken


class TokenMapper:
    def map_token_to_dto(self, token: AccessToken) -> TokenDto:
        return TokenDto(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            is_active=token.is_active,
            created_at=token.created_at,
        )
