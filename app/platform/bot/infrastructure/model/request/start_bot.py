from pydantic import BaseModel


class StartBotRequest(BaseModel):
    channel_name: str
