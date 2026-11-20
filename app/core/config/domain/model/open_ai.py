from dataclasses import dataclass


@dataclass(frozen=True)
class OpenAIConfig:
    api_key: str | None
    model: str | None
    proxy_url: str | None = None
