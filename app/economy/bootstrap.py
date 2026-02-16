from dataclasses import dataclass

from fastapi import Depends
from sqlalchemy.orm import Session

from app.economy.domain.economy_policy import EconomyPolicy
from app.economy.infrastructure.economy_repository import EconomyRepositoryImpl
from core.db import get_db_ro
from core.provider import Provider


@dataclass
class EconomyProviders:
    economy_policy_provider: Provider[EconomyPolicy]


def build_economy_providers() -> EconomyProviders:
    def economy_policy(db):
        return EconomyPolicy(EconomyRepositoryImpl(db))

    return EconomyProviders(economy_policy_provider=Provider(economy_policy))


def get_economy_policy_ro(db: Session = Depends(get_db_ro)) -> EconomyPolicy:
    return EconomyPolicy(EconomyRepositoryImpl(db))
