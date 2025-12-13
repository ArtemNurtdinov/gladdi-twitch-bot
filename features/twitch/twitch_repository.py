import json
from collections import Counter
from datetime import datetime
from sqlalchemy import func, case

from db.database import SessionLocal
from features.ai.ai_service import AIService
from features.ai.message import AIMessage, Role
from features.stream.db.stream_messages import TwitchMessage, ChatMessageLog
from features.minigame.word.db.word_history import WordHistory
from features.battle.db.battle_history import BattleHistory
from features.betting.db.bet_history import BetHistory
from features.stream.model.stream_statistics import StreamStatistics
from features.betting.model.rarity_level import RarityLevel
from features.battle.model.user_battle_stats import UserBattleStats


class TwitchService:
    _SYSTEM_PROMPT_FOR_GROUP = (
        "Ты — GLaDDi, цифровой ассистент нового поколения."
        "\nТы обладаешь характером GLaDOS, но являешься искусственным интеллектом мужского пола."
        "\n\nИнформация о твоем создателе:"
        "\nИмя: Артем"
        "\nДата рождения: 04.12.1992"
        "\nПол: мужской"
        "\nНикнейм на twitch: ArtemNeFRiT"
        "\nОбщая информация: Более 10 лет опыта в разработке программного обеспечения. Увлекается AI и NLP. Любит играть в игры на ПК, иногда проводит стримы на Twitch."
        "\n- Twitch канал: https://www.twitch.tv/artemnefrit"
        "\n- Instagram: https://www.instagram.com/artem_nfrt/profilecard"
        "\n- Steam: https://steamcommunity.com/id/ArtNeFRiT"
        "\n- Telegram канал: https://t.me/artem_nefrit_gaming"
        "\n- Любимые игры: World of Warcraft, Cyberpunk 2077, Skyrim, CS2, Clair Obscur: Expedition 33"
        "\n\nТвоя задача — взаимодействие с чатом на Twitch. Модераторы канала: d3ar_88, voidterror. Vip-пользователи канала: dankar1000, gidrovlad, vrrrrrrredinka, rympelina"
        "\n\nОтвечай с юмором в стиле GLaDOS, не уступай, подкалывай, но оставайся полезным."
        "\nНе обсуждай политические темы, интим и криминал."
        "\nОтвечай кратко."
    )

    def __init__(self, ai_repository: AIService):
        self.ai_repository = ai_repository

    def generate_response_in_chat(self, prompt: str, channel_name: str) -> str:
        db = SessionLocal()
        try:
            role_order = case((TwitchMessage.role == Role.USER, 2), (TwitchMessage.role == Role.ASSISTANT, 1), else_=3)

            non_system_messages = (
                db.query(TwitchMessage)
                .filter_by(channel_name=channel_name)
                .filter(TwitchMessage.role != Role.SYSTEM)
                .order_by(TwitchMessage.created_at.desc(), role_order)
                .limit(50)
                .all()
            )

            non_system_messages.reverse()

            system_prompt = self._SYSTEM_PROMPT_FOR_GROUP
            ai_messages = [AIMessage(Role.SYSTEM, system_prompt)]

            for message in non_system_messages:
                ai_messages.append(AIMessage(message.role, message.content))

            ai_messages.append(AIMessage(Role.USER, prompt))

            assistant_message = self.ai_repository.generate_ai_response(ai_messages)
            return assistant_message
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

    def get_used_words(self, channel_name: str, limit: int = 50) -> list[str]:
        db = SessionLocal()
        try:
            q = (
                db.query(WordHistory.word)
                .filter(WordHistory.channel_name == channel_name)
                .order_by(WordHistory.created_at.desc())
            )
            if limit and limit > 0:
                q = q.limit(limit)
            rows = q.all()
            # rows is list of tuples like [('слово',), ...]
            words = [row[0].lower() for row in rows]
            # Сохраняем порядок по времени (последние сверху), но удалим дубли, сохраняя первый встретившийся
            seen = set()
            unique_in_order = []
            for w in words:
                if w not in seen:
                    seen.add(w)
                    unique_in_order.append(w)
            return unique_in_order
        finally:
            db.close()

    def add_used_word(self, channel_name: str, word: str) -> None:
        normalized = "".join(ch for ch in str(word).lower() if ch.isalpha())
        if not normalized:
            return
        db = SessionLocal()
        try:
            record = WordHistory(channel_name=channel_name, word=normalized)
            db.add(record)
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def log_chat_message(self, channel_name: str, user: str, content: str):
        db = SessionLocal()

        try:
            normalized_user = user.lower()
            
            msg = ChatMessageLog(channel_name=channel_name, user_name=normalized_user, content=content,created_at=datetime.utcnow())
            db.add(msg)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()

    def get_top_chat_user_for_all_time(self, channel_name: str) -> str | None:
        db = SessionLocal()
        try:
            top = (
                db.query(ChatMessageLog.user_name)
                .filter(ChatMessageLog.channel_name == channel_name)
                .group_by(ChatMessageLog.user_name)
                .order_by(func.count(ChatMessageLog.id).desc())
                .limit(1)
                .first()
            )
            return top[0] if top else None

        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении сообщения: {e}")
        finally:
            db.close()

    def save_battle_history(self, channel_name: str, opponent_1: str, opponent_2: str, winner: str, result_text: str):
        db = SessionLocal()
        try:
            battle = BattleHistory(
                channel_name=channel_name,
                opponent_1=opponent_1,
                opponent_2=opponent_2,
                winner=winner,
                result_text=result_text
            )
            db.add(battle)
            db.commit()
        except Exception as e:
            db.rollback()
            raise Exception(f"Ошибка при сохранении истории битвы: {e}")
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

            return StreamStatistics(
                total_messages=total_messages,
                unique_users=unique_users,
                top_user=top_user,
                total_battles=total_battles,
                top_winner=top_winner
            )
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
                return UserBattleStats(total_battles=0, wins=0,losses=0, win_rate=0.0)

            total_battles = len(battles)
            wins = sum(1 for battle in battles if battle.winner == user_name)
            losses = total_battles - wins
            win_rate = (wins / total_battles) * 100 if total_battles > 0 else 0.0

            return UserBattleStats(total_battles=total_battles, wins=wins, losses=losses, win_rate=win_rate)
        finally:
            db.close()

    def suggest_word_and_hint_from_chat(self, channel_name: str, avoid_words: list[str] | None = None) -> tuple[str, str]:
        avoid_words = avoid_words or []
        if avoid_words:
            avoid_clause = "\n\nНе используй ранее загаданные слова (избегай повторов): " + ", ".join(sorted(set(avoid_words)))
        else:
            avoid_clause = ""

        db = SessionLocal()
        try:
            messages = (
                db.query(ChatMessageLog)
                .filter(ChatMessageLog.channel_name == channel_name)
                .order_by(ChatMessageLog.created_at.desc())
                .limit(100)
                .all()
            )

            messages.reverse()
            chat_text = "\n".join(f"{m.user_name}: {m.content}" for m in messages)

            instruction = (
                "Проанализируй последние сообщения из чата и выбери одно подходящее русское существительное (ОДНО слово),"
                " связанное по смыслу с обсуждаемыми темами. Придумай короткую подсказку-описание к нему. Не повторяйся в загаданных словах." +
                avoid_clause +
                "\nОтвет верни строго в JSON без дополнительного текста: {\"word\": \"слово\", \"hint\": \"краткая подсказка\"}.\n"
                "Требования: слово только из букв, без пробелов и дефисов; подсказка до 100 символов.\n\n"
                "Вот сообщения чата (ник: текст):\n" + chat_text
            )

            system_prompt = self._SYSTEM_PROMPT_FOR_GROUP
            ai_messages = [AIMessage(Role.SYSTEM, system_prompt), AIMessage(Role.USER, instruction)]
            response = self.ai_repository.generate_ai_response(ai_messages)

            self.save_conversation_to_db(channel_name, instruction, response)

            try:
                data = json.loads(response)
                word = str(data.get("word", "")).strip()
                hint = str(data.get("hint", "")).strip()
            except Exception:
                parts = response.split("|", 1)
                word = parts[0].strip() if parts else ""
                hint = parts[1].strip() if len(parts) > 1 else ""

            cleaned_word = "".join(ch for ch in word if ch.isalpha())
            if not cleaned_word:
                cleaned_word = "бот"
            if len(cleaned_word) < 3:
                cleaned_word = (cleaned_word + "бот")[:3]
            final_word = cleaned_word.lower()
            return final_word, hint or "Слово связано с последними темами чата"
        finally:
            db.close()
