from abc import ABC, abstractmethod


class PlatformAuth(ABC):
    def __init__(self, access_token: str, refresh_token: str, client_id: str, client_secret: str):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.client_id = client_id
        self.client_secret = client_secret

    def update_tokens(self, access_token: str, refresh_token: str):
        self.access_token = access_token
        self.refresh_token = refresh_token

    @abstractmethod
    async def update_access_token(self) -> None: ...

    @abstractmethod
    async def check_token_is_valid(self) -> bool: ...
