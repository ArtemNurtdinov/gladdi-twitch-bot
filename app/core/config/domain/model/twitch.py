from dataclasses import dataclass


@dataclass(frozen=True)
class TwitchConfig:
    client_id: str
    client_secret: str
    redirect_url: str
    channel_name: str
