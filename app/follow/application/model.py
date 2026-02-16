from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.follow.application.user_balance_port import BalanceDetail
from app.follow.application.user_sessions_port import SessionDetail
from app.follow.domain.models import ChannelFollower


@dataclass
class FollowerDetailResult:
    follower: ChannelFollower
    balance: BalanceDetail
    sessions: list[SessionDetail]


@dataclass(frozen=True)
class FollowersSyncJobDTO:
    channel_name: str
    occurred_at: datetime


@dataclass(frozen=True)
class ChannelFollowerDTO:
    user_id: str
    user_name: str
    display_name: str
    followed_at: datetime
