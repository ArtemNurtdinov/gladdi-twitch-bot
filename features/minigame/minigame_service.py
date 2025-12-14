import random
import logging
from typing import Optional, Dict
from datetime import datetime, timedelta

from features.minigame.number.model.guess_number_game import GuessNumberGame
from features.minigame.word.model.word_guess_game import WordGuessGame
from features.minigame.rps.model.rps_game import RPSGame, RPS_CHOICES
from features.economy.economy_service import EconomyService
from features.economy.db.transaction_history import TransactionType

logger = logging.getLogger(__name__)


class MinigameService:
    GUESS_GAME_DURATION_MINUTES = 5
    GUESS_GAME_PRIZE = 1000
    GUESS_MIN_NUMBER = 1
    GUESS_MAX_NUMBER = 100
    GUESS_PRIZE_DECREASE_PER_ATTEMPT = 50

    WORD_GAME_DURATION_MINUTES = 5
    WORD_GAME_MIN_PRIZE = 300
    WORD_GAME_MAX_PRIZE = 1000
    WORD_GAME_LETTER_REWARD_DECREASE = 100

    RPS_GAME_DURATION_MINUTES = 2
    RPS_BASE_BANK = 500
    RPS_ENTRY_FEE_PER_USER = 50

    FIRST_GAME_START_MIN = 5
    FIRST_GAME_START_MAX = 30

    GAME_START_INTERVAL_MIN = 30
    GAME_START_INTERVAL_MAX = 60
    
    def __init__(self, economy_service: EconomyService):
        self.economy_service = economy_service
        self.active_games: Dict[str, GuessNumberGame] = {}
        self.active_word_games: Dict[str, WordGuessGame] = {}
        self.active_rps_games: Dict[str, RPSGame] = {}
        self.last_game_time: Dict[str, datetime] = {}
        self.stream_start_time: Dict[str, datetime] = {}
        
    def set_stream_start_time(self, channel_name: str, start_time: datetime) -> None:
        self.stream_start_time[channel_name] = start_time
        
    def reset_stream_state(self, channel_name: str) -> None:
        if channel_name in self.stream_start_time:
            del self.stream_start_time[channel_name]

        if channel_name in self.active_games:
            self._finish_game_timeout(channel_name)
        if channel_name in self.active_word_games:
            self._finish_word_game_timeout(channel_name)
        if channel_name in self.active_rps_games:
            self._finish_rps_timeout(channel_name)
        
    def should_start_new_game(self, channel_name: str) -> bool:
        if channel_name in self.active_games or channel_name in self.active_word_games or channel_name in self.active_rps_games:
            return False

        current_time = datetime.utcnow()

        if channel_name not in self.last_game_time:
            if channel_name not in self.stream_start_time:
                return False
                
            stream_start = self.stream_start_time[channel_name]
            time_since_stream_start = current_time - stream_start

            first_game_delay_minutes = random.randint(self.FIRST_GAME_START_MIN, self.FIRST_GAME_START_MAX)
            required_delay = timedelta(minutes=first_game_delay_minutes)
            
            logger.debug(f"Проверка первой игры для {channel_name}: прошло {time_since_stream_start}, нужно {required_delay}")
            return time_since_stream_start >= required_delay

        last_game = self.last_game_time[channel_name]
        time_since_last = current_time - last_game

        random_minutes = random.randint(self.GAME_START_INTERVAL_MIN, self.GAME_START_INTERVAL_MAX)
        required_interval = timedelta(minutes=random_minutes)
        
        logger.debug(f"Проверка следующей игры для {channel_name}: прошло {time_since_last}, нужно {required_interval}")
        return time_since_last >= required_interval
    
    def start_guess_number_game(self, channel_name: str) -> GuessNumberGame:
        if channel_name in self.active_games:
            raise ValueError(f"Игра уже активна в канале {channel_name}")

        target_number = random.randint(self.GUESS_MIN_NUMBER, self.GUESS_MAX_NUMBER)

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.GUESS_GAME_DURATION_MINUTES)

        game = GuessNumberGame(
            channel_name=channel_name,
            target_number=target_number,
            start_time=start_time,
            end_time=end_time,
            min_number=self.GUESS_MIN_NUMBER,
            max_number=self.GUESS_MAX_NUMBER,
            prize_amount=self.GUESS_GAME_PRIZE
        )
        
        self.active_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        
        logger.info(f"Запущена игра 'угадай число' в канале {channel_name}. Загаданное число: {target_number}")
        
        return game
    
    def get_active_game(self, channel_name: str) -> Optional[GuessNumberGame]:
        return self.active_games.get(channel_name)
    
    def process_guess(self, channel_name: str, user_name: str, guess: int) -> tuple[bool, str]:
        if channel_name not in self.active_games:
            return False, "❌ Сейчас нет активной игры 'угадай число'"
        
        game = self.active_games[channel_name]

        if game.is_expired():
            self._finish_game_timeout(channel_name)
            return False, f"⏰ Время игры истекло! Загаданное число было {game.target_number}"

        if not game.is_active:
            return False, "❌ Игра уже завершена"

        if not game.is_valid_guess(guess):
            return False, f"❌ Число должно быть от {game.min_number} до {game.max_number}"

        if game.is_correct_guess(guess):
            return self._finish_game_with_winner(channel_name, user_name, guess)
        else:
            if game.prize_amount > 300:
                game.prize_amount = max(300, game.prize_amount - self.GUESS_PRIZE_DECREASE_PER_ATTEMPT)
            hint = "больше" if guess < game.target_number else "меньше"
            time_left = game.get_time_left_display()
            return False, f"❌ @{user_name}, не угадал! Загаданное число {hint} {guess}. Осталось: {time_left}"
    
    def _finish_game_with_winner(self, channel_name: str, winner_name: str, winning_number: int) -> tuple[bool, str]:
        game = self.active_games[channel_name]
        game.finish_game(winner_name)

        try:
            winner_balance = self.economy_service.add_balance(channel_name, winner_name, game.prize_amount, TransactionType.MINIGAME_WIN,
                                                              f"Победа в игре 'угадай число': {winning_number}")
            
            success_message = (f"🎉 ПОЗДРАВЛЯЕМ! @{winner_name} угадал число {winning_number} и "
                             f"выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет")
            
            logger.info(f"Игра 'угадай число' завершена в канале {channel_name}. "
                       f"Победитель: {winner_name}, число: {winning_number}, приз: {game.prize_amount}")

            del self.active_games[channel_name]
            
            return True, success_message
            
        except Exception as e:
            logger.error(f"Ошибка при начислении приза победителю {winner_name}: {e}")
            game.timeout_game()
            del self.active_games[channel_name]
            return False, f"❌ Ошибка при начислении приза. Игра завершена."
    
    def _finish_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_games:
            return "Игра не найдена"
        
        game = self.active_games[channel_name]
        game.timeout_game()
        
        timeout_message = f"⏰ Время игры 'угадай число' истекло! Загаданное число было {game.target_number}. Никто не выиграл на этот раз."
        
        logger.info(f"Игра 'угадай число' завершена по таймауту. Число: {game.target_number}")

        del self.active_games[channel_name]
        
        return timeout_message
    
    def check_expired_games(self) -> Dict[str, str]:
        expired_messages: Dict[str, str] = {}

        for channel_name in list(self.active_games.keys()):
            game = self.active_games.get(channel_name)
            if game and game.is_expired() and game.is_active:
                timeout_message = self._finish_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        for channel_name in list(self.active_word_games.keys()):
            game = self.active_word_games.get(channel_name)
            if game and game.is_expired() and game.is_active:
                timeout_message = self._finish_word_game_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        for channel_name in list(self.active_rps_games.keys()):
            game = self.active_rps_games.get(channel_name)
            if game and game.is_expired() and game.is_active:
                timeout_message = self._finish_rps_timeout(channel_name)
                expired_messages[channel_name] = timeout_message

        return expired_messages
    
    def get_game_status(self, channel_name: str) -> Optional[str]:
        if channel_name not in self.active_games:
            return None
        
        game = self.active_games[channel_name]
        
        if game.is_expired():
            return self._finish_game_timeout(channel_name)
        
        return game.get_game_summary()
    
    def force_end_game(self, channel_name: str) -> str:
        if channel_name not in self.active_games:
            return "❌ Нет активной игры для завершения"
        
        return self._finish_game_timeout(channel_name) 

    def start_word_guess_game(self, channel_name: str, word: str, hint: str) -> WordGuessGame:
        if channel_name in self.active_word_games:
            raise ValueError(f"Словесная игра уже активна в канале {channel_name}")

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.WORD_GAME_DURATION_MINUTES)
        game = WordGuessGame(
            channel_name=channel_name,
            target_word=word,
            hint=hint,
            start_time=start_time,
            end_time=end_time,
            prize_amount=self.WORD_GAME_MAX_PRIZE,
        )
        self.active_word_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        logger.info(
            f"Запущена игра 'поле чудес' в канале {channel_name}. Слово: {word}, подсказка: {hint}"
        )
        return game

    def process_letter(self, channel_name: str, user_name: str, letter: str) -> tuple[bool, str]:
        if channel_name not in self.active_word_games:
            return False, "❌ Сейчас нет активной игры 'поле чудес'"

        game = self.active_word_games[channel_name]
        if game.is_expired():
            self._finish_word_game_timeout(channel_name)
            return False, f"⏰ Время игры истекло! Слово было '{game.target_word}'"
        if not game.is_active:
            return False, "❌ Игра уже завершена"
        if not game.is_valid_letter_guess(letter):
            return False, "❌ Введите одну букву русского алфавита"

        was_revealed = game.reveal_letter(letter)
        masked = game.get_masked_word()
        time_left = game.get_time_left_display()

        if was_revealed:
            # Decrease prize for correct unique letter reveal
            if game.prize_amount > self.WORD_GAME_MIN_PRIZE:
                game.prize_amount = max(self.WORD_GAME_MIN_PRIZE, game.prize_amount - self.WORD_GAME_LETTER_REWARD_DECREASE)

            if game.all_letters_revealed():
                return self._finish_word_game_with_winner(channel_name, user_name)

            return False, f"✅ Буква есть! Слово: {masked}. Осталось: {time_left}"
        else:
            return False, f"❌ Такой буквы нет. Слово: {masked}. Осталось: {time_left}"

    def process_word(self, channel_name: str, user_name: str, word: str) -> tuple[bool, str]:
        if channel_name not in self.active_word_games:
            return False, "❌ Сейчас нет активной игры 'поле чудес'"
        game = self.active_word_games[channel_name]
        if game.is_expired():
            self._finish_word_game_timeout(channel_name)
            return False, f"⏰ Время игры истекло! Слово было '{game.target_word}'"
        if not game.is_active:
            return False, "❌ Игра уже завершена"

        if game.is_correct_word_guess(word):
            return self._finish_word_game_with_winner(channel_name, user_name)
        else:
            masked = game.get_masked_word()
            time_left = game.get_time_left_display()
            return False, f"❌ Неверное слово. Слово: {masked}. Осталось: {time_left}"

    def get_word_game_status(self, channel_name: str) -> Optional[str]:
        if channel_name not in self.active_word_games:
            return None
        game = self.active_word_games[channel_name]
        if game.is_expired():
            return self._finish_word_game_timeout(channel_name)
        return game.get_game_summary()

    def _finish_word_game_with_winner(self, channel_name: str, winner_name: str) -> tuple[bool, str]:
        game = self.active_word_games[channel_name]
        game.finish_game(winner_name)
        try:
            winner_balance = self.economy_service.add_balance(
                channel_name,
                winner_name,
                game.prize_amount,
                TransactionType.MINIGAME_WIN,
                f"Победа в игре 'поле чудес'"
            )
            success_message = (
                f"🎉 ПОЗДРАВЛЯЕМ! @{winner_name} угадал слово '{game.target_word}' и "
                f"выиграл {game.prize_amount} монет! Баланс: {winner_balance.balance} монет"
            )
            logger.info(
                f"Игра 'поле чудес' завершена. Победитель: {winner_name}, слово: {game.target_word}, приз: {game.prize_amount}"
            )
            del self.active_word_games[channel_name]
            return True, success_message
        except Exception as e:
            logger.error(f"Ошибка при начислении приза победителю {winner_name}: {e}")
            game.timeout_game()
            del self.active_word_games[channel_name]
            return False, "❌ Ошибка при начислении приза. Игра завершена."

    def _finish_word_game_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_word_games:
            return "Игра не найдена"
        game = self.active_word_games[channel_name]
        game.timeout_game()
        timeout_message = f"⏰ Время игры 'поле чудес' истекло! Слово было '{game.target_word}'. Никто не выиграл."
        logger.info(f"Игра 'поле чудес' завершена по таймауту. Слово: {game.target_word}")
        del self.active_word_games[channel_name]
        return timeout_message 

    def start_rps_game(self, channel_name: str) -> RPSGame:
        if channel_name in self.active_rps_games:
            raise ValueError(f"Игра 'камень-ножницы-бумага' уже активна в канале {channel_name}")
        start_time = datetime.utcnow()
        end_time = start_time + timedelta(minutes=self.RPS_GAME_DURATION_MINUTES)
        game = RPSGame(channel_name=channel_name, start_time=start_time, end_time=end_time, bank=self.RPS_BASE_BANK)
        self.active_rps_games[channel_name] = game
        self.last_game_time[channel_name] = start_time
        logger.info(f"Запущена игра 'камень-ножницы-бумага' в канале {channel_name}")
        return game

    def join_rps(self, channel_name: str, user_name: str, choice: str) -> tuple[bool, str]:
        if channel_name not in self.active_rps_games:
            return False, "❌ Сейчас нет активной игры 'камень-ножницы-бумага'"
        game = self.active_rps_games[channel_name]
        if game.is_expired():
            self._finish_rps_timeout(channel_name)
            return False, "⏰ Время игры истекло!"
        if not game.is_active:
            return False, "❌ Игра уже завершена"

        normalized_choice = choice.strip().lower()
        if normalized_choice not in RPS_CHOICES:
            return False, "❌ Выберите: камень, ножницы или бумага"

        normalized_user = user_name.lower()
        if normalized_user in game.user_choices:
            existing = game.user_choices[normalized_user]
            return False, f"❌ Вы уже выбрали: {existing}. Сменить нельзя в текущей игре"

        user_balance = self.economy_service.subtract_balance(channel_name, user_name, self.RPS_ENTRY_FEE_PER_USER, TransactionType.SPECIAL_EVENT,
                                                             "Участие в игре 'камень-ножницы-бумага'")
        if not user_balance:
            return False, f"❌ Недостаточно средств! Требуется {self.RPS_ENTRY_FEE_PER_USER} монет"
        game.bank += self.RPS_ENTRY_FEE_PER_USER

        game.set_choice(user_name, normalized_choice)
        return True, f"✅ Принято: @{user_name} — {normalized_choice}. Участников: {game.get_participants_count()}"

    def finish_rps(self, channel_name: str) -> tuple[bool, str]:
        if channel_name not in self.active_rps_games:
            return False, "Игра не найдена"
        game = self.active_rps_games[channel_name]
        if not game.is_active:
            return False, "Игра уже завершена"

        bot_choice = random.choice(RPS_CHOICES)
        counter_map = {
            "камень": "бумага",
            "бумага": "ножницы",
            "ножницы": "камень",
        }
        winning_choice = counter_map[bot_choice]
        game.winner_choice = winning_choice
        winners = game.get_winners()

        if winners:
            share = max(1, game.bank // len(winners))
            for winner in winners:
                self.economy_service.add_balance(channel_name, winner, share, TransactionType.MINIGAME_WIN, f"Победа в КНБ ({winning_choice})")
            winners_display = ", ".join(f"@{winner}" for winner in winners)
            message = (f"🤖 Выбор бота: {bot_choice}. 🏆 Побеждает вариант: {winning_choice}. "
                       f"Победители: {winners_display}. Банк: {game.bank} монет, каждому по {share}.")
        else:
            message = (f"🤖 Выбор бота: {bot_choice}. 🏆 Побеждает вариант: {winning_choice}. "
                       f"Победителей нет. Банк {game.bank} монет сгорает.")

        game.finish_game()
        del self.active_rps_games[channel_name]
        logger.info(f"Игра 'камень-ножницы-бумага' завершена в канале {channel_name}: {message}")
        return True, message

    def _finish_rps_timeout(self, channel_name: str) -> str:
        if channel_name not in self.active_rps_games:
            return "Игра не найдена"
        success, message = self.finish_rps(channel_name)
        return message 