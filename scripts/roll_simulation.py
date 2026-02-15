"""
Скрипт симуляции команды ставки (рулетка): прогоняет N спинов без БД и выводит метрики.
Запуск из корня проекта: python -m scripts.roll_simulation
"""
import random
import time
from dataclasses import dataclass

from app.betting.application.betting_service import BettingService
from app.betting.domain.models import EmojiConfig, RarityLevel


@dataclass
class MockBettingRepo:
    def save_bet_history(self, channel_name: str, user_name: str, slot_result: str, result_type: str, rarity_level: RarityLevel) -> None:
        pass

    def get_user_bets(self, channel_name: str, user_name: str) -> list:
        return []


def run_one_spin(bet_amount: int, betting_service: BettingService) -> tuple[str, str, RarityLevel, int]:
    """Один спин: возвращает (slot_result_string, result_type, rarity_level, payout)."""
    emojis = EmojiConfig.get_emojis_list()
    weights = EmojiConfig.get_weights_list()
    slot_results = random.choices(emojis, weights=weights, k=3)
    slot_result_string = EmojiConfig.format_slot_result(slot_results)

    unique_results = set(slot_results)
    if len(unique_results) == 1:
        result_type = "jackpot"
    elif len(unique_results) == 2:
        result_type = "partial"
    else:
        result_type = "miss"

    rarity_level = betting_service.determine_correct_rarity(slot_result=slot_result_string, result_type=result_type)

    base_payout = BettingService.RARITY_MULTIPLIERS.get(rarity_level, 0.2) * bet_amount
    if result_type == "jackpot":
        payout = base_payout * BettingService.JACKPOT_MULTIPLIER
    elif result_type == "partial":
        payout = base_payout * BettingService.PARTIAL_MULTIPLIER
    else:
        payout = 0
    payout = int(payout) if payout > 0 else 0

    return slot_result_string, result_type, rarity_level, payout


def main() -> None:
    total_rolls = 1_000_000
    bet_amount = BettingService.BET_COST  # 50

    betting_service = BettingService(repo=MockBettingRepo())

    total_wagered = 0
    total_payout = 0
    result_counts: dict[str, int] = {"jackpot": 0, "partial": 0, "miss": 0}
    rarity_counts: dict[RarityLevel, int] = {r: 0 for r in RarityLevel}
    payouts_by_type: dict[str, list[int]] = {"jackpot": [], "partial": [], "miss": []}
    max_payout = 0
    max_payout_roll: tuple[str, str, RarityLevel, int] | None = None

    print(f"Симуляция: {total_rolls:,} ставок по {bet_amount} монет (без экипировки)")
    print("Старт...")
    start = time.perf_counter()

    for i in range(total_rolls):
        _, result_type, rarity_level, payout = run_one_spin(bet_amount, betting_service)
        total_wagered += bet_amount
        total_payout += payout
        result_counts[result_type] += 1
        rarity_counts[rarity_level] += 1
        payouts_by_type[result_type].append(payout)
        if payout > max_payout:
            max_payout = payout
            max_payout_roll = (_, result_type, rarity_level, payout)

        if (i + 1) % 200_000 == 0:
            elapsed = time.perf_counter() - start
            print(f"  {i + 1:,} / {total_rolls:,} ({elapsed:.1f} с)")

    elapsed = time.perf_counter() - start
    profit = total_payout - total_wagered
    rtp = (total_payout / total_wagered * 100) if total_wagered else 0

    print()
    print("=" * 60)
    print("МЕТРИКИ СИМУЛЯЦИИ СТАВКИ (РУЛЕТКА)")
    print("=" * 60)
    print(f"Всего спинов:        {total_rolls:,}")
    print(f"Ставка за спин:      {bet_amount} монет")
    print(f"Всего поставлено:    {total_wagered:,} монет")
    print(f"Всего выиграно:      {total_payout:,} монет")
    print(f"Прибыль/убыток:      {profit:+,} монет")
    print(f"RTP (return to player): {rtp:.2f}%")
    print(f"Время выполнения:    {elapsed:.2f} с ({total_rolls / elapsed:,.0f} спинов/с)")
    print()

    print("По типу результата:")
    for result_type in ("jackpot", "partial", "miss"):
        count = result_counts[result_type]
        pct = count / total_rolls * 100
        payouts_list = payouts_by_type[result_type]
        total_this = sum(payouts_list)
        avg_payout = total_this / len(payouts_list) if payouts_list else 0
        print(f"  {result_type:8} — {count:>10,} ({pct:>5.2f}%)  сумма выплат: {total_this:>12,}  средний выигрыш: {avg_payout:>8.1f}")
    print()

    print("По редкости (определённой для исхода):")
    for r in RarityLevel:
        count = rarity_counts[r]
        pct = count / total_rolls * 100
        print(f"  {r.value:12} — {count:>10,} ({pct:>5.2f}%)")
    print()

    if max_payout_roll:
        _, mt, mr, mp = max_payout_roll
        print(f"Максимальный выигрыш за спин: {max_payout:,} монет (тип: {mt}, редкость: {mr.value})")
    print("=" * 60)


if __name__ == "__main__":
    main()
