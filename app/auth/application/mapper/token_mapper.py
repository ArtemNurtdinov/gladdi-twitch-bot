from app.auth.application.model.token import TokenDTO
from app.auth.domain.model.access_token import AccessToken


class TokenMapper:
    def map_token_to_dto(self, token: AccessToken) -> TokenDTO:
        return TokenDTO(
            id=token.id,
            user_id=token.user_id,
            token=token.token,
            expires_at=token.expires_at,
            is_active=token.is_active,
            created_at=token.created_at,
        )
