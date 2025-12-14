from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
from db.base import SessionLocal
from features.stream.db.stream_messages import ChatMessageLog


class DashboardService:

    def __init__(self):
        self.channel_name = "artemnefrit"

    def get_top_users(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            user_stats = (
                db.query(
                    ChatMessageLog.user_name,
                    func.count(ChatMessageLog.id).label('message_count')
                )
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .group_by(ChatMessageLog.user_name)
                .order_by(func.count(ChatMessageLog.id).desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "username": stat.user_name,
                    "message_count": stat.message_count
                }
                for stat in user_stats
            ]
        finally:
            db.close()
