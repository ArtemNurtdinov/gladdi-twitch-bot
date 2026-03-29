from dataclasses import dataclass


@dataclass(frozen=True)
class ApplicationConfig:
    host: str
    port: int
    auth_secret: str
    auth_secret_algorithm: str
    access_token_expire_minutes: int
