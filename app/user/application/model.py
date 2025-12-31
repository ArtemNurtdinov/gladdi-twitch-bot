from dataclasses import dataclass


@dataclass(frozen=True)
class UserInfoDTO:
    id: str
    login: str
    display_name: str
