import random
import sys
import time
from collections import defaultdict
sys.path.append('.')

from features.betting.model.emoji_config import EmojiConfig
from features.betting.model.rarity_level import RarityLevel
import argparse
import math


def determine_result_rarity(slot_results, result_type):
    """Определяет редкость результата согласно логике EconomyService"""
    
    if result_type == "jackpot":
        return EmojiConfig.get_emoji_rarity(slot_results[0])
    
    elif result_type == "partial":
        # Находим повторяющийся эмодзи (2 шт)
        repeated_emoji = None
        for emoji in slot_results:
            if slot_results.count(emoji) == 2:
                repeated_emoji = emoji
                break
        
        if not repeated_emoji:
            return EmojiConfig.get_emoji_rarity(slot_results[0])
        
        # Находим уникальный эмодзи (1 шт)
        unique_emoji = None
        for emoji in slot_results:
            if slot_results.count(emoji) == 1:
                unique_emoji = emoji
                break
        
        repeated_rarity = EmojiConfig.get_emoji_rarity(repeated_emoji)
        unique_rarity = EmojiConfig.get_emoji_rarity(unique_emoji) if unique_emoji else RarityLevel.COMMON
        
        rarity_priority = {
            RarityLevel.COMMON: 1,
            RarityLevel.UNCOMMON: 2,
            RarityLevel.RARE: 3,
            RarityLevel.EPIC: 4,
            RarityLevel.LEGENDARY: 5,
            RarityLevel.MYTHICAL: 6
        }
        
        if rarity_priority[repeated_rarity] >= rarity_priority[unique_rarity]:
            return repeated_rarity
        else:
            return unique_rarity
    
    else:  # miss
        # Соответствует EconomyService._determine_correct_rarity для miss:
        max_rarity = RarityLevel.COMMON
        for emoji in slot_results:
            emoji_rarity = EmojiConfig.get_emoji_rarity(emoji)
            if emoji_rarity == RarityLevel.MYTHICAL:
                max_rarity = RarityLevel.MYTHICAL
                break
            elif emoji_rarity == RarityLevel.LEGENDARY and max_rarity != RarityLevel.MYTHICAL:
                max_rarity = RarityLevel.LEGENDARY
            elif emoji_rarity == RarityLevel.EPIC and max_rarity not in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                max_rarity = RarityLevel.EPIC
            elif emoji_rarity == RarityLevel.RARE and max_rarity not in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY, RarityLevel.EPIC]:
                max_rarity = RarityLevel.RARE
            elif emoji_rarity == RarityLevel.UNCOMMON and max_rarity == RarityLevel.COMMON:
                max_rarity = RarityLevel.UNCOMMON
        return max_rarity


def calculate_payout(result_type, rarity_level, bet_amount, jackpot_bonus: float = 1.0, partial_bonus: float = 1.0, miss_bonus: float = 1.0):
    """Рассчитывает выплату согласно системе EconomyService, с учётом дополнительных множителей."""
    
    RARITY_MULTIPLIERS = {
        RarityLevel.COMMON: 0.2,
        RarityLevel.UNCOMMON: 0.4,
        RarityLevel.RARE: 0.6,
        RarityLevel.EPIC: 1,
        RarityLevel.LEGENDARY: 5,
        RarityLevel.MYTHICAL: 100
    }
    
    JACKPOT_MULTIPLIER = 7
    PARTIAL_MULTIPLIER = 2
    
    CONSOLATION_PRIZES = {
        RarityLevel.MYTHICAL: 5000,
        RarityLevel.LEGENDARY: 50,
        RarityLevel.EPIC: 25,
        RarityLevel.RARE: 0,
        RarityLevel.UNCOMMON: 0,
        RarityLevel.COMMON: 0
    }
    
    base_payout = RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
    
    if result_type == "jackpot":
        return base_payout * JACKPOT_MULTIPLIER * jackpot_bonus
    elif result_type == "partial":
        return base_payout * PARTIAL_MULTIPLIER * partial_bonus
    else:  # miss
        consolation_prize = CONSOLATION_PRIZES.get(rarity_level, 0)
        if consolation_prize > 0:
            return max(consolation_prize, bet_amount * 0.1) * miss_bonus
        else:
            return 0


def test_chair_combinations_with_balance(num_trials=1000000, bet_amount=100, starting_balance=1000000,
                                          with_gambler_amulet: bool = False,
                                          gambler_jackpot_mult: float = 5.0,
                                          gambler_partial_mult: float = 5.0,
                                          gambler_miss_mult: float = 1.0):
    """Симуляция слот-машины с балансом и детальной статистикой, с опцией амулета лудомана."""
    
    emojis = EmojiConfig.get_emojis_list()
    weights = EmojiConfig.get_weights_list()
    
    print("🎰 СИМУЛЯЦИЯ СЛОТ-МАШИНЫ С ДЕТАЛЬНОЙ СТАТИСТИКОЙ ДЖЕКПОТОВ 🎰")
    print("=" * 70)
    print(f"💰 Стартовый баланс: {starting_balance:,}")
    print(f"🎲 Количество ставок: {num_trials:,}")
    print(f"💸 Размер ставки: {bet_amount}")
    print(f"💵 Общая сумма ставок: {num_trials * bet_amount:,}")
    print(f"🎰 Амулет лудомана: {'ВКЛ' if with_gambler_amulet else 'ВЫКЛ'} (jackpot x{gambler_jackpot_mult}, partial x{gambler_partial_mult})")
    
    print("\nЭмодзи и их веса:")
    for emoji, weight in zip(emojis, weights):
        rarity = EmojiConfig.get_emoji_rarity(emoji)
        print(f"  {emoji}: {weight} ({rarity.value})")
    
    print(f"\nОбщий вес: {sum(weights)}")
    
    # Основные счетчики
    jackpots = 0
    partials = 0
    misses = 0
    dino_count = 0
    
    # Расширенная аналитика
    result_stats = {
        "jackpot": {"count": 0, "total_payout": 0},
        "partial": {"count": 0, "total_payout": 0},
        "miss": {"count": 0, "total_payout": 0},
    }
    payout_values = []  # только положительные выплаты
    partial_payouts = []  # (payout, slot_result_string, rarity, bet_index)
    current_miss_streak = 0
    max_miss_streak = 0
    current_win_streak = 0
    max_win_streak = 0
    
    # Экономические счетчики
    balance = starting_balance
    total_bet = 0
    total_payout = 0
    biggest_win = 0
    biggest_win_combo = ""
    bankruptcy_bet = 0
    
    # Влияние амулета
    amulet_extra_payout_total = 0
    
    # Таймауты (для miss)
    timeouts_count = 0
    timeouts_seconds_total = 0
    avoided_timeouts_count = 0
    avoided_timeouts_seconds_total = 0
    
    # НОВОЕ: Детальная статистика джекпотов
    jackpot_stats = defaultdict(int)  # Сколько раз каждый эмодзи дал джекпот
    jackpot_payouts = defaultdict(list)  # Все выплаты по каждому джекпоту
    jackpot_log = []  # Полный лог всех джекпотов с деталями
    total_jackpot_payout = 0
    
    # Статистика по редкостям
    rarity_stats = {rarity: {"count": 0, "total_payout": 0} for rarity in RarityLevel}
    
    print(f"\nЗапуск симуляции {num_trials:,} ставок...")
    start_time = time.time()
    
    for i in range(num_trials):
        if i % 100000 == 0 and i > 0:
            progress = i/num_trials*100
            print(f"Обработано: {i:,} / {num_trials:,} ({progress:.1f}%) | Баланс: {balance:,} | Джекпоты: {jackpots}")
        
        # Проверяем, хватает ли денег на ставку
        if balance < bet_amount:
            bankruptcy_bet = i + 1
            print(f"\n💸 БАНКРОТСТВО на ставке #{bankruptcy_bet:,}!")
            break
        
        # Делаем ставку
        balance -= bet_amount
        total_bet += bet_amount
        
        # Крутим слот
        slot_results = random.choices(emojis, weights=weights, k=3)
        slot_result_string = EmojiConfig.format_slot_result(slot_results)
        
        # Определяем тип результата
        unique_results = set(slot_results)
        if len(unique_results) == 1:
            result_type = "jackpot"
            jackpots += 1
            
            # НОВОЕ: Логируем джекпот
            jackpot_emoji = slot_results[0]
            jackpot_stats[jackpot_emoji] += 1
            
        elif len(unique_results) == 2:
            result_type = "partial"
            partials += 1
        else:
            result_type = "miss"
            misses += 1
        
        # Определяем редкость
        rarity = determine_result_rarity(slot_results, result_type)
        rarity_stats[rarity]["count"] += 1
        
        # Рассчитываем выплату
        base_payout_without_amulet = calculate_payout(result_type, rarity, bet_amount)
        payout = calculate_payout(
            result_type,
            rarity,
            bet_amount,
            jackpot_bonus=(gambler_jackpot_mult if with_gambler_amulet else 1.0),
            partial_bonus=(gambler_partial_mult if with_gambler_amulet else 1.0),
            miss_bonus=(gambler_miss_mult if with_gambler_amulet else 1.0)
        )
        
        # Применяем выплату и учитываем вклад амулета
        balance += payout
        total_payout += payout
        rarity_stats[rarity]["total_payout"] += payout
        if with_gambler_amulet and payout > base_payout_without_amulet:
            amulet_extra_payout_total += (payout - base_payout_without_amulet)
        
        # Агрегируем статистику по типам и стрики
        result_stats[result_type]["count"] += 1
        result_stats[result_type]["total_payout"] += payout
        if payout > 0:
            payout_values.append(payout)
        if result_type == "partial" and payout > 0:
            partial_payouts.append((payout, slot_result_string, rarity.value, i + 1))
        
        if result_type == "miss":
            current_miss_streak += 1
            max_miss_streak = max(max_miss_streak, current_miss_streak)
            current_win_streak = 0
        else:
            current_win_streak += 1
            max_win_streak = max(max_win_streak, current_win_streak)
            current_miss_streak = 0
        
        # Таймауты для miss по правилам EconomyService
        if result_type == "miss":
            # Если есть консольный приз (для некоторых редкостей), таймауты зависят от редкости; иначе 180с
            CONSOLATION_PRIZES = {
                RarityLevel.MYTHICAL: 100,
                RarityLevel.LEGENDARY: 50,
                RarityLevel.EPIC: 25,
                RarityLevel.RARE: 0,
                RarityLevel.UNCOMMON: 0,
                RarityLevel.COMMON: 0
            }
            consolation_prize = CONSOLATION_PRIZES.get(rarity, 0)
            if consolation_prize > 0:
                if rarity in [RarityLevel.MYTHICAL, RarityLevel.LEGENDARY]:
                    timeout_seconds = 0
                elif rarity == RarityLevel.EPIC:
                    timeout_seconds = 60
                else:
                    timeout_seconds = 120
            else:
                timeout_seconds = 180
            
            if timeout_seconds > 0:
                timeouts_count += 1
                timeouts_seconds_total += timeout_seconds
                if with_gambler_amulet:
                    avoided_timeouts_count += 1
                    avoided_timeouts_seconds_total += timeout_seconds
        
        # НОВОЕ: Дополнительная информация для джекпотов
        if result_type == "jackpot":
            total_jackpot_payout += payout
            jackpot_payouts[jackpot_emoji].append(payout)
            
            # Сохраняем детали джекпота
            jackpot_log.append({
                "bet_number": i + 1,
                "emoji": jackpot_emoji,
                "rarity": rarity.value,
                "payout": payout,
                "balance_after": balance
            })
        
        # Отслеживаем самый большой выигрыш
        if payout > biggest_win:
            biggest_win = payout
            biggest_win_combo = f"{slot_result_string} ({result_type}, {rarity.value})"
        
        # Подсчет мифических
        if 'DinoDance' in slot_results:
            dino_count += 1
    
    end_time = time.time()
    actual_bets = bankruptcy_bet if bankruptcy_bet > 0 else num_trials
    
    print(f"\n🎯 РЕЗУЛЬТАТЫ СИМУЛЯЦИИ")
    print("=" * 70)
    print(f"⏱️  Время выполнения: {end_time - start_time:.2f} секунд")
    print(f"🎲 Сделано ставок: {actual_bets:,}")
    
    print(f"\n💰 ЭКОНОМИКА:")
    print(f"💸 Потрачено на ставки: {total_bet:,}")
    print(f"💵 Получено выплат: {total_payout:,}")
    print(f"📊 Итоговый баланс: {balance:,}")
    profit_loss = balance - starting_balance
    profit_percentage = (profit_loss / starting_balance) * 100
    rtp = (total_payout / total_bet) * 100 if total_bet > 0 else 0
    print(f"📈 Прибыль/Убыток: {profit_loss:+,} ({profit_percentage:+.2f}%)")
    print(f"🎰 RTP (Return to Player): {rtp:.2f}%")
    print(f"🏆 Самый большой выигрыш: {biggest_win:,} ({biggest_win_combo})")
    if with_gambler_amulet:
        print(f"🎁 Доп. выплаты от амулета: {amulet_extra_payout_total:,}")
        print(f"ΔRTP от амулета: {amulet_extra_payout_total / total_bet * 100:.2f}%")
        if total_payout > 0:
            print(f"Доля амулета в выплатах: {amulet_extra_payout_total / total_payout * 100:.2f}%")
    
    # Распределение выплат
    if payout_values:
        payout_values_sorted = sorted(payout_values)
        n = len(payout_values_sorted)
        mean_payout = sum(payout_values_sorted) / n
        variance = sum((x - mean_payout) ** 2 for x in payout_values_sorted) / n
        stddev = math.sqrt(variance)
        def q(p):
            idx = int(p * (n - 1))
            return payout_values_sorted[idx]
        print("\n📈 Распределение выплат (по выигрышам):")
        print(f"P50: {q(0.50):,.0f} | P90: {q(0.90):,.0f} | P99: {q(0.99):,.0f} | MAX: {payout_values_sorted[-1]:,}")
        print(f"Среднее: {mean_payout:,.2f} | StdDev: {stddev:,.2f}")
    
    # Статистика по типам результатов
    print("\n📊 По типам результатов:")
    for rt in ["jackpot", "partial", "miss"]:
        cnt = result_stats[rt]["count"]
        total = result_stats[rt]["total_payout"]
        avg = (total / cnt) if cnt > 0 else 0
        print(f"{rt}: {cnt:,} шт | Выплаты: {total:,} | Средняя выплата: {avg:,.2f}")
    
    if bankruptcy_bet > 0:
        print(f"💸 Банкротство произошло на ставке #{bankruptcy_bet:,}")
    
    # НОВОЕ: Детальная статистика джекпотов
    print(f"\n🎰 ДЕТАЛЬНАЯ СТАТИИСТИКА ДЖЕКПОТОВ")
    print("=" * 50)
    print(f"🎯 Всего джекпотов: {jackpots:,}")
    print(f"💰 Общая выплата джекпотов: {total_jackpot_payout:,}")
    print(f"📊 Средняя выплата джекпота: {total_jackpot_payout/jackpots:.1f}" if jackpots > 0 else "")
    print(f"🎲 Частота джекпотов: 1 к {actual_bets/jackpots:.0f}" if jackpots > 0 else "")
    
    print(f"\n🏅 ДЖЕКПОТЫ ПО ЭМОДЗИ:")
    if jackpot_stats:
        sorted_jackpots = sorted(jackpot_stats.items(), key=lambda x: x[1], reverse=True)
        for emoji, count in sorted_jackpots:
            rarity = EmojiConfig.get_emoji_rarity(emoji)
            frequency = actual_bets / count if count > 0 else 0
            avg_payout = sum(jackpot_payouts[emoji]) / len(jackpot_payouts[emoji])
            total_from_emoji = sum(jackpot_payouts[emoji])
            print(f"  {emoji} ({rarity.value}): {count:,} раз (1 к {frequency:.0f}) | Ср.выплата: {avg_payout:,.0f} | Итого: {total_from_emoji:,}")
    
    # Топ-джекпоты и partial
    if jackpot_log:
        # Топ-5 самых больших джекпотов
        biggest_jackpots = sorted(jackpot_log, key=lambda x: x['payout'], reverse=True)[:5]
        print(f"\n💎 ТОП-5 САМЫХ БОЛЬШИХ ДЖЕКПОТОВ:")
        for i, jp in enumerate(biggest_jackpots, 1):
            print(f"  {i}. #{jp['bet_number']:,}: {jp['emoji']} ({jp['rarity']}) → {jp['payout']:,} монет")
    if partial_payouts:
        biggest_partials = sorted(partial_payouts, key=lambda x: x[0], reverse=True)[:5]
        print(f"\n✨ ТОП-5 САМЫХ БОЛЬШИХ PARTIAL ВЫПЛАТ:")
        for i, (p, combo, rarity, bet_idx) in enumerate(biggest_partials, 1):
            print(f"  {i}. #{bet_idx:,}: {combo} ({rarity}) → {p:,} монет")
    
    print(f"\n📊 ОБЩАЯ СТАТИСТИКА:")
    print(f"Джекпоты (3 одинаковых): {jackpots:,} ({jackpots/actual_bets*100:.4f}%)")
    print(f"Partial (2 одинаковых): {partials:,} ({partials/actual_bets*100:.4f}%)")
    print(f"Промахи: {misses:,} ({misses/actual_bets*100:.4f}%)")
    print(f"Макс серия промахов: {max_miss_streak:,}")
    print(f"Макс серия выигрышей (jackpot/partial/консольные призы): {max_win_streak:,}")
    
    print(f"\n🦕 МИФИЧЕСКИЕ:")
    print(f"DinoDance выпадений: {dino_count:,} ({dino_count/actual_bets*100:.6f}%)")
    
    print(f"\n💎 СТАТИСТИКА ПО РЕДКОСТЯМ:")
    for rarity in RarityLevel:
        count = rarity_stats[rarity]["count"]
        payout = rarity_stats[rarity]["total_payout"]
        if count > 0:
            avg_payout = payout / count
            print(f"{rarity.value}: {count:,} раз ({count/actual_bets*100:.4f}%) | Выплаты: {payout:,} | Среднее: {avg_payout:.1f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Симуляция слот-машины и анализ статистики")
    parser.add_argument("--num-trials", type=int, default=1000000, help="Количество ставок")
    parser.add_argument("--bet-amount", type=int, default=100, help="Размер одной ставки")
    parser.add_argument("--starting-balance", type=int, default=1000000, help="Стартовый баланс")
    parser.add_argument("--amulet", action="store_true", help="Включить эффект амулета лудомана")
    parser.add_argument("--amulet-jackpot-mult", type=float, default=1.5, help="Множитель джекпота от амулета")
    parser.add_argument("--amulet-partial-mult", type=float, default=1.1, help="Множитель partial от амулета")
    parser.add_argument("--amulet-miss-mult", type=float, default=0.1, help="Множитель промаха (консольного приза) от амулета")

    args = parser.parse_args()

    test_chair_combinations_with_balance(
        num_trials=args.num_trials,
        bet_amount=args.bet_amount,
        starting_balance=args.starting_balance,
        with_gambler_amulet=args.amulet,
        gambler_jackpot_mult=args.amulet_jackpot_mult,
        gambler_partial_mult=args.amulet_partial_mult,
        gambler_miss_mult=args.amulet_miss_mult,
    ) 