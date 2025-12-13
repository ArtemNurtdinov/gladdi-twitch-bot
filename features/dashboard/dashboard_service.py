from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from collections import Counter
from sqlalchemy import func, case
from db.base import SessionLocal
from features.stream.db.stream_messages import ChatMessageLog, TwitchMessage
from features.battle.db.battle_history import BattleHistory
from features.betting.db.bet_history import BetHistory
from features.economy.db.user_balance import UserBalance
from features.economy.db.transaction_history import TransactionHistory, TransactionType
from features.stream.db.stream import Stream
from features.stream.db.stream_viewer_session import StreamViewerSession
from features.betting.model.rarity_level import RarityLevel
from features.ai.message import Role


class DashboardService:

    def __init__(self):
        self.channel_name = "artemnefrit"

    def get_chat_activity_by_hour(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .all()
            )

            hourly_activity = {}
            for hour in range(24):
                hourly_activity[hour] = 0

            for message in messages:
                hour = message.created_at.hour
                hourly_activity[hour] += 1

            return {
                "labels": [f"{hour:02d}:00" for hour in range(24)],
                "data": [hourly_activity[hour] for hour in range(24)],
                "total_messages": len(messages)
            }
        finally:
            db.close()

    def get_daily_activity(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            daily_stats = (
                db.query(
                    func.date(ChatMessageLog.created_at).label('date'),
                    func.count(ChatMessageLog.id).label('message_count'),
                    func.count(func.distinct(ChatMessageLog.user_name)).label('unique_users')
                )
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .group_by(func.date(ChatMessageLog.created_at))
                .order_by(func.date(ChatMessageLog.created_at))
                .all()
            )

            date_range = []
            current_date = since.date()
            end_date = datetime.utcnow().date()

            while current_date <= end_date:
                date_range.append(current_date)
                current_date += timedelta(days=1)

            daily_data = {stat.date: {"messages": stat.message_count, "users": stat.unique_users}
                          for stat in daily_stats}

            labels = []
            messages_data = []
            users_data = []

            for date in date_range:
                labels.append(date.strftime("%d.%m"))
                data = daily_data.get(date, {"messages": 0, "users": 0})
                messages_data.append(data["messages"])
                users_data.append(data["users"])

            return {
                "labels": labels,
                "messages": messages_data,
                "users": users_data
            }
        finally:
            db.close()

    def get_top_users(self, days: int = 30, limit: int = 10) -> List[Dict[str, Any]]:
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

    def get_battle_statistics(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            battles = (
                db.query(BattleHistory)
                .filter(BattleHistory.channel_name == self.channel_name)
                .filter(BattleHistory.created_at >= since)
                .all()
            )

            winners = [battle.winner for battle in battles]
            winner_counts = Counter(winners)

            participants = []
            for battle in battles:
                participants.extend([battle.opponent_1, battle.opponent_2])
            participant_counts = Counter(participants)

            daily_battles = {}
            for battle in battles:
                date = battle.created_at.date()
                daily_battles[date] = daily_battles.get(date, 0) + 1

            return {
                "total_battles": len(battles),
                "top_winners": [
                    {"username": winner, "wins": count}
                    for winner, count in winner_counts.most_common(10)
                ],
                "top_participants": [
                    {"username": participant, "battles": count}
                    for participant, count in participant_counts.most_common(10)
                ],
                "daily_battles": {date.strftime("%Y-%m-%d"): count for date, count in daily_battles.items()}
            }
        finally:
            db.close()

    def get_ai_interaction_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            twitch_interactions = (
                db.query(TwitchMessage)
                .filter(TwitchMessage.channel_name == self.channel_name)
                .filter(TwitchMessage.created_at >= since)
                .filter(TwitchMessage.role == Role.USER)
                .count()
            )

            return {
                "twitch_interactions": twitch_interactions,
                "total_interactions": twitch_interactions
            }
        finally:
            db.close()

    def get_overview_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            total_messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .count()
            )

            unique_users = (
                db.query(func.count(func.distinct(ChatMessageLog.user_name)))
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .scalar()
            )

            total_battles = (
                db.query(BattleHistory)
                .filter(BattleHistory.channel_name == self.channel_name)
                .filter(BattleHistory.created_at >= since)
                .count()
            )

            total_bets = (
                db.query(BetHistory)
                .filter(BetHistory.channel_name == self.channel_name)
                .filter(BetHistory.created_at >= since)
                .count()
            )

            mythical_events = (
                db.query(BetHistory)
                .filter(BetHistory.channel_name == self.channel_name)
                .filter(BetHistory.created_at >= since)
                .filter(BetHistory.rarity_level == RarityLevel.MYTHICAL)
                .count()
            )

            ai_stats = self.get_ai_interaction_stats(days)

            avg_messages_per_day = total_messages / days if days > 0 else 0
            avg_users_per_day = unique_users / days if days > 0 else 0
            avg_bets_per_day = total_bets / days if days > 0 else 0

            return {
                "total_messages": total_messages,
                "unique_users": unique_users,
                "total_battles": total_battles,
                "total_bets": total_bets,
                "mythical_events": mythical_events,
                "ai_interactions": ai_stats["total_interactions"],
                "avg_messages_per_day": round(avg_messages_per_day, 1),
                "avg_users_per_day": round(avg_users_per_day, 1),
                "avg_bets_per_day": round(avg_bets_per_day, 1),
                "period_days": days
            }
        finally:
            db.close()

    def get_user_activity_heatmap(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == self.channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .all()
            )

            heatmap_data = []
            weekdays = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']

            for day in range(7):
                day_data = []
                for hour in range(24):
                    count = sum(1 for msg in messages
                                if msg.created_at.weekday() == day and msg.created_at.hour == hour)
                    day_data.append(count)
                heatmap_data.append(day_data)

            return {
                "data": heatmap_data,
                "weekdays": weekdays,
                "hours": [f"{h:02d}:00" for h in range(24)]
            }
        finally:
            db.close()

    def get_chat_messages(self, page: int = 1, limit: int = 50, user_filter: Optional[str] = None, date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            query = db.query(ChatMessageLog).filter(ChatMessageLog.channel_name == self.channel_name)

            if user_filter:
                query = query.filter(ChatMessageLog.user_name.ilike(f"%{user_filter}%"))

            if date_from:
                query = query.filter(ChatMessageLog.created_at >= date_from)

            if date_to:
                query = query.filter(ChatMessageLog.created_at <= date_to)

            total_count = query.count()

            offset = (page - 1) * limit
            messages = (
                query.order_by(ChatMessageLog.created_at.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.id,
                    "user_name": msg.user_name,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "created_at_formatted": msg.created_at.strftime("%d.%m.%Y %H:%M:%S")
                })

            return {
                "messages": formatted_messages,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
        finally:
            db.close()

    def get_twitch_ai_messages(self, page: int = 1, limit: int = 50, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            query = db.query(TwitchMessage).filter(TwitchMessage.channel_name == self.channel_name)

            if date_from:
                query = query.filter(TwitchMessage.created_at >= date_from)

            if date_to:
                query = query.filter(TwitchMessage.created_at <= date_to)

            total_count = query.count()

            offset = (page - 1) * limit
            messages = (
                query.order_by(TwitchMessage.created_at.asc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            formatted_messages = []
            for msg in messages:
                formatted_messages.append({
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "created_at_formatted": msg.created_at.strftime("%d.%m.%Y %H:%M:%S")
                })

            return {
                "messages": formatted_messages,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
        finally:
            db.close()

    def get_mythical_events(self, days: int = 30) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            mythical_bets = (
                db.query(BetHistory)
                .filter(BetHistory.channel_name == self.channel_name)
                .filter(BetHistory.created_at >= since)
                .filter(BetHistory.rarity_level == RarityLevel.MYTHICAL)
                .order_by(BetHistory.created_at.desc())
                .all()
            )

            return [
                {
                    "username": bet.user_name,
                    "slot_result": bet.slot_result,
                    "result_type": bet.result_type,
                    "rarity_level": bet.rarity_level.value,
                    "created_at": bet.created_at.strftime("%Y-%m-%d %H:%M:%S")
                }
                for bet in mythical_bets
            ]
        finally:
            db.close()

    def get_lucky_users(self, days: int = 30, min_bets: int = 5) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            user_stats = (
                db.query(
                    BetHistory.user_name,
                    func.count(BetHistory.id).label('total_bets'),
                    func.sum(case((BetHistory.result_type == 'jackpot', 1), else_=0)).label('jackpots'),
                    func.sum(case((BetHistory.rarity_level == RarityLevel.MYTHICAL, 1), else_=0)).label('mythical_count')
                )
                .filter(BetHistory.channel_name == self.channel_name)
                .filter(BetHistory.created_at >= since)
                .group_by(BetHistory.user_name)
                .having(func.count(BetHistory.id) >= min_bets)
                .all()
            )

            lucky_users = []
            for stat in user_stats:
                jackpot_rate = (stat.jackpots / stat.total_bets) * 100 if stat.total_bets > 0 else 0
                mythical_rate = (stat.mythical_count / stat.total_bets) * 100 if stat.total_bets > 0 else 0

                lucky_users.append({
                    "username": stat.user_name,
                    "total_bets": stat.total_bets,
                    "jackpots": stat.jackpots,
                    "mythical_count": stat.mythical_count,
                    "jackpot_rate": jackpot_rate,
                    "mythical_rate": mythical_rate
                })

            lucky_users.sort(key=lambda x: x['jackpot_rate'], reverse=True)

            return lucky_users[:10]
        finally:
            db.close()

    def get_bet_hourly_activity(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            bets = (
                db.query(BetHistory)
                .filter(BetHistory.channel_name == self.channel_name)
                .filter(BetHistory.created_at >= since)
                .all()
            )

            hourly_activity = {}
            for hour in range(24):
                hourly_activity[hour] = 0

            for bet in bets:
                hour = bet.created_at.hour
                hourly_activity[hour] += 1

            return {
                "labels": [f"{hour:02d}:00" for hour in range(24)],
                "data": [hourly_activity[hour] for hour in range(24)],
                "total_bets": len(bets)
            }
        finally:
            db.close()

    def get_user_balance_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            users = (
                db.query(UserBalance)
                .filter(UserBalance.channel_name == self.channel_name)
                .filter(UserBalance.is_active == True)
                .all()
            )

            if not users:
                return {
                    "total_users": 0,
                    "total_balance": 0,
                    "avg_balance": 0,
                    "median_balance": 0,
                    "total_earned": 0,
                    "total_spent": 0,
                    "avg_earned": 0,
                    "avg_spent": 0,
                    "active_users": 0,
                    "rich_users_count": 0,
                    "poor_users_count": 0
                }

            balances = [user.balance for user in users]
            total_earned = sum(user.total_earned for user in users)
            total_spent = sum(user.total_spent for user in users)

            balances.sort()
            median_balance = balances[len(balances) // 2] if balances else 0

            rich_users = sum(1 for balance in balances if balance > 10000)
            poor_users = sum(1 for balance in balances if balance < 1000)

            return {
                "total_users": len(users),
                "total_balance": sum(balances),
                "avg_balance": sum(balances) / len(balances) if balances else 0,
                "median_balance": median_balance,
                "total_earned": total_earned,
                "total_spent": total_spent,
                "avg_earned": total_earned / len(users) if users else 0,
                "avg_spent": total_spent / len(users) if users else 0,
                "active_users": len(users),
                "rich_users_count": rich_users,
                "poor_users_count": poor_users
            }
        finally:
            db.close()

    def get_top_users_by_balance(self, limit: int = 10) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            users = (
                db.query(UserBalance)
                .filter(UserBalance.channel_name == self.channel_name)
                .filter(UserBalance.is_active == True)
                .order_by(UserBalance.balance.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "username": user.user_name,
                    "balance": user.balance,
                    "total_earned": user.total_earned,
                    "total_spent": user.total_spent,
                    "net_profit": user.total_earned - user.total_spent,
                    "last_daily_claim": user.last_daily_claim.isoformat() if user.last_daily_claim else None,
                    "created_at": user.created_at.isoformat()
                }
                for user in users
            ]
        finally:
            db.close()

    def get_transaction_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            transactions = (
                db.query(TransactionHistory)
                .filter(TransactionHistory.channel_name == self.channel_name)
                .filter(TransactionHistory.created_at >= since)
                .all()
            )

            if not transactions:
                return {
                    "total_transactions": 0,
                    "unique_users": 0,
                    "total_volume": 0,
                    "positive_volume": 0,
                    "negative_volume": 0,
                    "avg_transaction": 0,
                    "transaction_types": {},
                    "daily_transactions": {}
                }

            type_counts = {}
            type_volumes = {}
            for transaction_type in TransactionType:
                count = sum(1 for t in transactions if t.transaction_type == transaction_type)
                volume = sum(t.amount for t in transactions if t.transaction_type == transaction_type)
                if count > 0:
                    type_counts[transaction_type.value] = count
                    type_volumes[transaction_type.value] = volume

            daily_transactions = {}
            for transaction in transactions:
                date = transaction.created_at.date()
                daily_transactions[date] = daily_transactions.get(date, 0) + 1

            positive_volume = sum(t.amount for t in transactions if t.amount > 0)
            negative_volume = sum(t.amount for t in transactions if t.amount < 0)
            total_volume = sum(abs(t.amount) for t in transactions)

            return {
                "total_transactions": len(transactions),
                "unique_users": len(set(t.user_name for t in transactions)),
                "total_volume": total_volume,
                "positive_volume": positive_volume,
                "negative_volume": abs(negative_volume),
                "avg_transaction": total_volume / len(transactions) if transactions else 0,
                "transaction_types": type_counts,
                "transaction_volumes": type_volumes,
                "daily_transactions": {date.strftime("%Y-%m-%d"): count for date, count in daily_transactions.items()}
            }
        finally:
            db.close()

    def get_user_transactions(self, user_name: str, page: int = 1, limit: int = 1000, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            query = (
                db.query(TransactionHistory)
                .filter(TransactionHistory.channel_name == self.channel_name)
                .filter(TransactionHistory.user_name == user_name)
                .filter(TransactionHistory.created_at >= since)
            )

            total_count = query.count()

            offset = (page - 1) * limit
            transactions = (
                query.order_by(TransactionHistory.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            formatted_transactions = []
            for transaction in transactions:
                formatted_transactions.append({
                    "id": transaction.id,
                    "transaction_type": transaction.transaction_type.value,
                    "amount": transaction.amount,
                    "balance_before": transaction.balance_before,
                    "balance_after": transaction.balance_after,
                    "description": transaction.description,
                    "created_at": transaction.created_at.isoformat(),
                    "created_at_formatted": transaction.created_at.strftime("%d.%m.%Y %H:%M:%S")
                })

            return {
                "transactions": formatted_transactions,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit,
                "username": user_name
            }
        finally:
            db.close()

    def get_economy_overview(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            balance_stats = self.get_user_balance_stats(days)
            transaction_stats = self.get_transaction_stats(days)

            since = datetime.utcnow() - timedelta(days=days)
            new_users = (
                db.query(UserBalance)
                .filter(UserBalance.channel_name == self.channel_name)
                .filter(UserBalance.created_at >= since)
                .count()
            )

            biggest_transaction = (
                db.query(TransactionHistory)
                .filter(TransactionHistory.channel_name == self.channel_name)
                .filter(TransactionHistory.created_at >= since)
                .filter(TransactionHistory.amount > 0)
                .order_by(TransactionHistory.amount.desc())
                .first()
            )

            biggest_loss = (
                db.query(TransactionHistory)
                .filter(TransactionHistory.channel_name == self.channel_name)
                .filter(TransactionHistory.created_at >= since)
                .filter(TransactionHistory.amount < 0)
                .order_by(TransactionHistory.amount.asc())
                .first()
            )

            return {
                "balance_stats": balance_stats,
                "transaction_stats": transaction_stats,
                "new_users": new_users,
                "biggest_win": {
                    "username": biggest_transaction.user_name if biggest_transaction else None,
                    "amount": biggest_transaction.amount if biggest_transaction else 0,
                    "type": biggest_transaction.transaction_type.value if biggest_transaction else None,
                    "description": biggest_transaction.description if biggest_transaction else None
                } if biggest_transaction else None,
                "biggest_loss": {
                    "username": biggest_loss.user_name if biggest_loss else None,
                    "amount": abs(biggest_loss.amount) if biggest_loss else 0,
                    "type": biggest_loss.transaction_type.value if biggest_loss else None,
                    "description": biggest_loss.description if biggest_loss else None
                } if biggest_loss else None,
                "period_days": days
            }
        finally:
            db.close()

    def get_richest_users_by_earnings(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            users = (
                db.query(UserBalance)
                .filter(UserBalance.channel_name == self.channel_name)
                .filter(UserBalance.is_active == True)
                .order_by(UserBalance.total_earned.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "username": user.user_name,
                    "total_earned": user.total_earned,
                    "total_spent": user.total_spent,
                    "net_profit": user.total_earned - user.total_spent,
                    "current_balance": user.balance,
                    "profit_ratio": (user.total_earned - user.total_spent) / user.total_earned if user.total_earned > 0 else 0
                }
                for user in users
            ]
        finally:
            db.close()

    def get_stream_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            streams = (
                db.query(Stream)
                .filter(Stream.channel_name == self.channel_name)
                .filter(Stream.created_at >= since)
                .all()
            )

            if not streams:
                return {
                    "total_streams": 0,
                    "active_streams": 0,
                    "completed_streams": 0,
                    "total_duration_minutes": 0,
                    "avg_duration_minutes": 0,
                    "total_viewers": 0,
                    "avg_viewers": 0,
                    "max_concurrent_viewers": 0,
                    "avg_concurrent_viewers": 0,
                    "popular_games": {},
                    "daily_streams": {}
                }

            active_streams = sum(1 for s in streams if s.is_active)
            completed_streams = len(streams) - active_streams

            total_duration = sum(s.get_duration_minutes() for s in streams)
            avg_duration = total_duration / len(streams) if streams else 0

            total_viewers = sum(s.total_viewers for s in streams)
            avg_viewers = total_viewers / len(streams) if streams else 0

            max_concurrent = max(s.max_concurrent_viewers for s in streams) if streams else 0
            avg_concurrent = sum(s.max_concurrent_viewers for s in streams) / len(streams) if streams else 0

            games = [s.game_name for s in streams if s.game_name]
            game_counts = Counter(games)
            popular_games = dict(game_counts.most_common(10))

            daily_streams = {}
            for stream in streams:
                date = stream.created_at.date()
                daily_streams[date] = daily_streams.get(date, 0) + 1

            return {
                "total_streams": len(streams),
                "active_streams": active_streams,
                "completed_streams": completed_streams,
                "total_duration_minutes": total_duration,
                "avg_duration_minutes": round(avg_duration, 1),
                "total_viewers": total_viewers,
                "avg_viewers": round(avg_viewers, 1),
                "max_concurrent_viewers": max_concurrent,
                "avg_concurrent_viewers": round(avg_concurrent, 1),
                "popular_games": popular_games,
                "daily_streams": {date.strftime("%Y-%m-%d"): count for date, count in daily_streams.items()}
            }
        finally:
            db.close()

    def get_stream_history(self, page: int = 1, limit: int = 10, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            query = (
                db.query(Stream)
                .filter(Stream.channel_name == self.channel_name)
                .filter(Stream.created_at >= since)
            )

            total_count = query.count()

            offset = (page - 1) * limit
            streams = (
                query.order_by(Stream.created_at.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )

            formatted_streams = []
            for stream in streams:
                formatted_streams.append({
                    "id": stream.id,
                    "title": stream.title,
                    "game_name": stream.game_name,
                    "started_at": stream.started_at.isoformat(),
                    "ended_at": stream.ended_at.isoformat() if stream.ended_at else None,
                    "duration_minutes": stream.get_duration_minutes(),
                    "duration_formatted": stream.get_formatted_duration(),
                    "total_viewers": stream.total_viewers,
                    "max_concurrent_viewers": stream.max_concurrent_viewers,
                    "is_active": stream.is_active,
                    "created_at": stream.created_at.isoformat(),
                    "created_at_formatted": stream.created_at.strftime("%d.%m.%Y %H:%M:%S")
                })

            return {
                "streams": formatted_streams,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit
            }
        finally:
            db.close()

    def get_stream_top_by_duration(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            streams = (
                db.query(Stream)
                .filter(Stream.channel_name == self.channel_name)
                .filter(Stream.created_at >= since)
                .filter(Stream.is_active == False)
                .all()
            )

            streams.sort(key=lambda x: x.get_duration_minutes(), reverse=True)

            return [
                {
                    "id": stream.id,
                    "title": stream.title,
                    "game_name": stream.game_name,
                    "started_at": stream.started_at.isoformat(),
                    "ended_at": stream.ended_at.isoformat() if stream.ended_at else None,
                    "duration_minutes": stream.get_duration_minutes(),
                    "duration_formatted": stream.get_formatted_duration(),
                    "total_viewers": stream.total_viewers,
                    "max_concurrent_viewers": stream.max_concurrent_viewers,
                    "is_active": stream.is_active,
                    "created_at": stream.created_at.isoformat(),
                    "created_at_formatted": stream.created_at.strftime("%d.%m.%Y %H:%M:%S")
                }
                for stream in streams[:limit]
            ]
        finally:
            db.close()

    def get_stream_top_by_viewers(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            streams = (
                db.query(Stream)
                .filter(Stream.channel_name == self.channel_name)
                .filter(Stream.created_at >= since)
                .order_by(Stream.max_concurrent_viewers.desc())
                .limit(limit)
                .all()
            )

            return [
                {
                    "id": stream.id,
                    "title": stream.title,
                    "game_name": stream.game_name,
                    "started_at": stream.started_at.isoformat(),
                    "ended_at": stream.ended_at.isoformat() if stream.ended_at else None,
                    "duration_minutes": stream.get_duration_minutes(),
                    "duration_formatted": stream.get_formatted_duration(),
                    "total_viewers": stream.total_viewers,
                    "max_concurrent_viewers": stream.max_concurrent_viewers,
                    "is_active": stream.is_active,
                    "created_at": stream.created_at.isoformat(),
                    "created_at_formatted": stream.created_at.strftime("%d.%m.%Y %H:%M:%S")
                }
                for stream in streams
            ]
        finally:
            db.close()

    def get_current_stream(self) -> Optional[Dict[str, Any]]:
        db = SessionLocal()
        try:
            stream = (
                db.query(Stream)
                .filter(Stream.channel_name == self.channel_name)
                .filter(Stream.is_active == True)
                .order_by(Stream.created_at.desc())
                .first()
            )

            if not stream:
                return None

            return {
                "id": stream.id,
                "title": stream.title,
                "game_name": stream.game_name,
                "started_at": stream.started_at.isoformat(),
                "duration_minutes": stream.get_duration_minutes(),
                "duration_formatted": stream.get_formatted_duration(),
                "total_viewers": stream.total_viewers,
                "max_concurrent_viewers": stream.max_concurrent_viewers,
                "is_active": stream.is_active,
                "created_at": stream.created_at.isoformat()
            }
        finally:
            db.close()

    def get_viewer_session_stats(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            sessions = (
                db.query(StreamViewerSession)
                .filter(StreamViewerSession.channel_name == self.channel_name)
                .filter(StreamViewerSession.created_at >= since)
                .all()
            )

            if not sessions:
                return {
                    "total_sessions": 0,
                    "unique_viewers": 0,
                    "active_sessions": 0,
                    "total_watch_time_minutes": 0,
                    "avg_session_duration": 0,
                    "total_rewards_claimed": 0,
                    "avg_rewards_per_user": 0,
                    "top_reward_thresholds": {},
                    "daily_sessions": {}
                }

            unique_viewers = len(set(s.user_name for s in sessions))
            active_sessions = sum(1 for s in sessions if s.is_watching)

            total_watch_time = sum(s.total_minutes for s in sessions)
            avg_duration = total_watch_time / len(sessions) if sessions else 0

            all_rewards = []
            for session in sessions:
                rewards = session.get_claimed_rewards_list()
                all_rewards.extend(rewards)

            total_rewards = len(all_rewards)
            avg_rewards = total_rewards / unique_viewers if unique_viewers > 0 else 0

            reward_counts = Counter(all_rewards)
            top_rewards = {str(k): v for k, v in reward_counts.most_common(10)}

            daily_sessions = {}
            for session in sessions:
                date = session.created_at.date()
                daily_sessions[date] = daily_sessions.get(date, 0) + 1

            return {
                "total_sessions": len(sessions),
                "unique_viewers": unique_viewers,
                "active_sessions": active_sessions,
                "total_watch_time_minutes": total_watch_time,
                "avg_session_duration": round(avg_duration, 1),
                "total_rewards_claimed": total_rewards,
                "avg_rewards_per_user": round(avg_rewards, 1),
                "top_reward_thresholds": top_rewards,
                "daily_sessions": {date.strftime("%Y-%m-%d"): count for date, count in daily_sessions.items()}
            }
        finally:
            db.close()

    def get_viewer_top_by_time(self, limit: int = 10, days: int = 30) -> List[Dict[str, Any]]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            user_stats = (
                db.query(
                    StreamViewerSession.user_name,
                    func.sum(StreamViewerSession.total_minutes).label('total_watch_time'),
                    func.count(StreamViewerSession.id).label('total_sessions'),
                    func.avg(StreamViewerSession.total_minutes).label('avg_session_duration')
                )
                .filter(StreamViewerSession.channel_name == self.channel_name)
                .filter(StreamViewerSession.created_at >= since)
                .group_by(StreamViewerSession.user_name)
                .order_by(func.sum(StreamViewerSession.total_minutes).desc())
                .limit(limit)
                .all()
            )

            result = []
            for stat in user_stats:
                user_sessions = (
                    db.query(StreamViewerSession)
                    .filter(StreamViewerSession.channel_name == self.channel_name)
                    .filter(StreamViewerSession.user_name == stat.user_name)
                    .filter(StreamViewerSession.created_at >= since)
                    .all()
                )

                all_rewards = []
                for session in user_sessions:
                    rewards = session.get_claimed_rewards_list()
                    all_rewards.extend(rewards)

                unique_rewards = len(set(all_rewards))

                result.append({
                    "username": stat.user_name,
                    "total_watch_time_minutes": stat.total_watch_time,
                    "total_watch_time_formatted": f"{stat.total_watch_time // 60}ч {stat.total_watch_time % 60}м",
                    "total_sessions": stat.total_sessions,
                    "avg_session_duration": round(stat.avg_session_duration, 1),
                    "total_rewards_claimed": len(all_rewards),
                    "unique_rewards": unique_rewards
                })

            return result
        finally:
            db.close()

    def get_viewer_session_rewards(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            sessions = (
                db.query(StreamViewerSession)
                .filter(StreamViewerSession.channel_name == self.channel_name)
                .filter(StreamViewerSession.created_at >= since)
                .filter(StreamViewerSession.rewards_claimed != '')
                .all()
            )

            if not sessions:
                return {
                    "total_rewards_given": 0,
                    "unique_reward_recipients": 0,
                    "reward_distribution": {},
                    "recent_rewards": [],
                    "avg_rewards_per_user": 0
                }

            all_rewards = []
            recent_rewards = []
            unique_recipients = set()

            for session in sessions:
                rewards = session.get_claimed_rewards_list()
                if rewards:
                    unique_recipients.add(session.user_name)
                    all_rewards.extend(rewards)

                    # Добавляем в недавние награды
                    if session.last_reward_claimed:
                        recent_rewards.append({
                            "username": session.user_name,
                            "reward_threshold": max(rewards),
                            "claimed_at": session.last_reward_claimed.isoformat(),
                            "claimed_at_formatted": session.last_reward_claimed.strftime("%d.%m.%Y %H:%M:%S")
                        })

            recent_rewards.sort(key=lambda x: x['claimed_at'], reverse=True)

            reward_counts = Counter(all_rewards)
            avg_rewards = len(all_rewards) / len(unique_recipients) if unique_recipients else 0

            return {
                "total_rewards_given": len(all_rewards),
                "unique_reward_recipients": len(unique_recipients),
                "reward_distribution": {str(k): v for k, v in sorted(reward_counts.items())},
                "recent_rewards": recent_rewards[:20],  # Последние 20 наград
                "avg_rewards_per_user": round(avg_rewards, 1)
            }
        finally:
            db.close()

    def get_viewer_session_activity(self, days: int = 30) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            sessions = (
                db.query(StreamViewerSession)
                .filter(StreamViewerSession.channel_name == self.channel_name)
                .filter(StreamViewerSession.created_at >= since)
                .all()
            )

            hourly_activity = {}
            for hour in range(24):
                hourly_activity[hour] = 0

            for session in sessions:
                if session.session_start:
                    hour = session.session_start.hour
                    hourly_activity[hour] += 1

            daily_activity = {}
            for session in sessions:
                date = session.created_at.date()
                if date not in daily_activity:
                    daily_activity[date] = {"sessions": 0, "watch_time": 0, "unique_users": set()}

                daily_activity[date]["sessions"] += 1
                daily_activity[date]["watch_time"] += session.total_minutes
                daily_activity[date]["unique_users"].add(session.user_name)

            formatted_daily = {}
            for date, data in daily_activity.items():
                formatted_daily[date.strftime("%Y-%m-%d")] = {
                    "sessions": data["sessions"],
                    "watch_time_minutes": data["watch_time"],
                    "unique_users": len(data["unique_users"])
                }

            return {
                "hourly_activity": {
                    "labels": [f"{hour:02d}:00" for hour in range(24)],
                    "data": [hourly_activity[hour] for hour in range(24)]
                },
                "daily_activity": formatted_daily,
                "total_sessions": len(sessions)
            }
        finally:
            db.close()
