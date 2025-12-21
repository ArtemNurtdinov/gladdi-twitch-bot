from enum import Enum


class Intent(Enum):
    GAMES_HISTORY = "games_history"
    JACKBOX = "jackbox"
    SKUF_FEMBOY = "skuf_femboy"
    DANKAR_CUT = "dankar_cut"
    HELLO = "hello"
    OTHER = "other"


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIMessage:

    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content
