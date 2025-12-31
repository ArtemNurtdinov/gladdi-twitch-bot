from enum import Enum


class Role(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class AIMessage:
    def __init__(self, role: Role, content: str):
        self.role = role
        self.content = content
