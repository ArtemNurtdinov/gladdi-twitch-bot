from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy import func, case

from db.base import SessionLocal
from features.ai.message import AIMessage, Role
from features.stream.db.stream_messages import TwitchMessage, ChatMessageLog
from features.battle.db.battle_history import BattleHistory
from features.betting.db.bet_history import BetHistory
from features.stream.model.stream_statistics import StreamStatistics
from features.betting.model.rarity_level import RarityLevel
from features.battle.model.user_battle_stats import UserBattleStats
from features.twitch.chat_schemas import TopChatUser


class ChatService:

    def get_last_ai_messages(self, channel_name: str, system_prompt: str) -> list[AIMessage]:
        db = SessionLocal()
        try:
            role_order = case((TwitchMessage.role == Role.USER, 2), (TwitchMessage.role == Role.ASSISTANT, 1), else_=3)

            messages = (
                db.query(TwitchMessage)
                .filter_by(channel_name=channel_name)
                .filter(TwitchMessage.role != Role.SYSTEM)
                .order_by(TwitchMessage.created_at.desc(), role_order)
                .limit(50)
                .all()
            )
            messages.reverse()
            ai_messages = [AIMessage(Role.SYSTEM, system_prompt)]

            for message in messages:
                ai_messages.append(AIMessage(message.role, message.content))
            return ai_messages
        finally:
            db.close()

    def save_conversation_to_db(self, channel_name: str, prompt: str, response: str):
        db = SessionLocal()

        try:
            user_message = TwitchMessage(channel_name=channel_name, role=Role.USER, content=prompt)
            ai_message = TwitchMessage(channel_name=channel_name, role=Role.ASSISTANT, content=response)

            db.add(user_message)
            db.add(ai_message)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()

    def save_chat_message(self, channel_name: str, user_name: str, content: str):
        db = SessionLocal()
        try:
            normalized_user = user_name.lower()
            msg = ChatMessageLog(channel_name=channel_name, user_name=normalized_user, content=content, created_at=datetime.utcnow())
            db.add(msg)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()

    def get_stream_statistics(self, channel_name: str, stream_start_time: datetime) -> StreamStatistics:
        stream_start_time = stream_start_time.replace(tzinfo=None)
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == channel_name)
                .filter(ChatMessageLog.created_at >= stream_start_time)
                .all()
            )
            total_messages = len(messages)
            unique_users = len(set(msg.user_name for msg in messages))

            user_counts = Counter(msg.user_name for msg in messages)
            if user_counts:
                top_user = user_counts.most_common(1)[0][0]
            else:
                top_user = None

            battles = (
                db.query(BattleHistory)
                .filter(BattleHistory.channel_name == channel_name)
                .filter(BattleHistory.created_at >= stream_start_time)
                .all()
            )
            total_battles = len(battles)
            if battles:
                winner_counts = Counter(b.winner for b in battles)
                top_winner = winner_counts.most_common(1)[0][0]
            else:
                top_winner = None

            return StreamStatistics(total_messages, unique_users, top_user, total_battles, top_winner)
        finally:
            db.close()

    def save_bet_history(self, channel_name: str, user_name: str, slot_result: str, result_type: str, rarity_level: RarityLevel):
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            bet = BetHistory(channel_name=channel_name, user_name=normalized_user_name, slot_result=slot_result, result_type=result_type, rarity_level=rarity_level)
            db.add(bet)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении истории ставки: {e}")
        finally:
            db.close()

    def get_user_bet_count(self, user_name: str, channel_name: str) -> int:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            count = (
                db.query(BetHistory)
                .filter(BetHistory.user_name == normalized_user_name)
                .filter(BetHistory.channel_name == channel_name)
                .count()
            )
            return count
        finally:
            db.close()

    def get_user_bet_stats(self, user_name: str, channel_name: str) -> dict:
        db = SessionLocal()
        try:
            normalized_user_name = user_name.lower()

            bets = (
                db.query(BetHistory)
                .filter(BetHistory.user_name == normalized_user_name)
                .filter(BetHistory.channel_name == channel_name)
                .all()
            )

            if not bets:
                return {
                    "total_bets": 0,
                    "jackpots": 0,
                    "partial_matches": 0,
                    "misses": 0,
                    "mythical_count": 0,
                    "common_count": 0,
                    "uncommon_count": 0,
                    "rare_count": 0,
                    "epic_count": 0,
                    "legendary_count": 0
                }

            total_bets = len(bets)
            jackpots = sum(1 for bet in bets if bet.result_type == "jackpot")
            partial_matches = sum(1 for bet in bets if bet.result_type == "partial")
            misses = sum(1 for bet in bets if bet.result_type == "miss")

            mythical_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.MYTHICAL)
            legendary_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.LEGENDARY)
            epic_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.EPIC)
            rare_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.RARE)
            uncommon_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.UNCOMMON)
            common_count = sum(1 for bet in bets if bet.rarity_level == RarityLevel.COMMON)

            return {
                "total_bets": total_bets,
                "jackpots": jackpots,
                "partial_matches": partial_matches,
                "misses": misses,
                "mythical_count": mythical_count,
                "legendary_count": legendary_count,
                "epic_count": epic_count,
                "rare_count": rare_count,
                "uncommon_count": uncommon_count,
                "common_count": common_count,
                "jackpot_rate": (jackpots / total_bets) * 100 if total_bets > 0 else 0,
                "mythical_rate": (mythical_count / total_bets) * 100 if total_bets > 0 else 0
            }
        finally:
            db.close()

    def get_user_battle_stats(self, user_name: str, channel_name: str) -> UserBattleStats:
        db = SessionLocal()
        try:
            battles = (
                db.query(BattleHistory)
                .filter(
                    ((BattleHistory.opponent_1 == user_name) | (BattleHistory.opponent_2 == user_name))
                    & (BattleHistory.channel_name == channel_name)
                )
                .all()
            )

            if not battles:
                return UserBattleStats(total_battles=0, wins=0, losses=0, win_rate=0.0)

            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == user_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0

            return UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)
        finally:
            db.close()

    def get_chat_messages(self, channel_name: str, from_time, to_time):
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == channel_name)
                .filter(ChatMessageLog.created_at >= from_time)
                .filter(ChatMessageLog.created_at < to_time)
                .order_by(ChatMessageLog.created_at.asc())
                .all()
            )
            return messages
        finally:
            db.close()

    def get_last_chat_messages(self, channel_name: str, limit: int):
        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == channel_name)
                .order_by(ChatMessageLog.created_at.desc())
                .limit(limit)
                .all()
            )
            messages.reverse()
            return messages
        finally:
            db.close()

    def get_top_chat_users(self, channel_name: str, days: int, limit: int) -> list[TopChatUser]:
        db = SessionLocal()
        try:
            since = datetime.utcnow() - timedelta(days=days)

            user_stats = (
                db.query(ChatMessageLog.user_name, func.count(ChatMessageLog.id).label('message_count'))
                .filter(ChatMessageLog.channel_name == channel_name)
                .filter(ChatMessageLog.created_at >= since)
                .group_by(ChatMessageLog.user_name)
                .order_by(func.count(ChatMessageLog.id).desc())
                .limit(limit)
                .all()
            )

            return [TopChatUser(username=stat.user_name, message_count=stat.message_count) for stat in user_stats]
        finally:
            db.close()
