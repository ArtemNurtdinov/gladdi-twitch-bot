from dataclasses import dataclass

from app.betting.domain.model.rarity import RarityLevel


@dataclass(frozen=True)
class Bet:
    id: int
    channel_name: str
    user_name: str
    slot_result: str
    result_type: str
    rarity_level: RarityLevel
