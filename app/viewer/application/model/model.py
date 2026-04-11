from dataclasses import dataclass


@dataclass(frozen=True)
class ViewerInfoDTO:
    id: str
    login: str
    display_name: str
