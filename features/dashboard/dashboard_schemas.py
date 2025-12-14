from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional


class OverviewStats(BaseModel):
    total_messages: int = Field(..., description="Общее количество сообщений")
    unique_users: int = Field(..., description="Количество уникальных пользователей")
    total_battles: int = Field(..., description="Общее количество битв")
    total_bets: int = Field(..., description="Общее количество ставок")
    mythical_events: int = Field(..., description="Количество мифических событий")
    ai_interactions: int = Field(..., description="Количество AI взаимодействий")
    avg_messages_per_day: float = Field(..., description="Среднее количество сообщений в день")
    avg_users_per_day: float = Field(..., description="Среднее количество пользователей в день")
    avg_bets_per_day: float = Field(..., description="Среднее количество ставок в день")
    period_days: int = Field(..., description="Период анализа в днях")


class HourlyActivity(BaseModel):
    labels: List[str] = Field(..., description="Метки времени (часы)")
    data: List[int] = Field(..., description="Количество сообщений по часам")
    total_messages: int = Field(..., description="Общее количество сообщений")


class DailyActivity(BaseModel):
    labels: List[str] = Field(..., description="Метки дат")
    messages: List[int] = Field(..., description="Количество сообщений по дням")
    users: List[int] = Field(..., description="Количество пользователей по дням")


class TopUser(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    message_count: int = Field(..., description="Количество сообщений")


class BattleWinner(BaseModel):
    username: str = Field(..., description="Имя победителя")
    wins: int = Field(..., description="Количество побед")


class BattleParticipant(BaseModel):
    username: str = Field(..., description="Имя участника")
    battles: int = Field(..., description="Количество битв")


class BattleStats(BaseModel):
    total_battles: int = Field(..., description="Общее количество битв")
    top_winners: List[BattleWinner] = Field(..., description="Топ победителей")
    top_participants: List[BattleParticipant] = Field(..., description="Топ участников")
    daily_battles: Dict[str, int] = Field(..., description="Битвы по дням")


class AIInteractionStats(BaseModel):
    twitch_interactions: int = Field(..., description="AI взаимодействия в Twitch")
    total_interactions: int = Field(..., description="Общее количество AI взаимодействий")


class ActivityHeatmap(BaseModel):
    data: List[List[int]] = Field(..., description="Матрица активности [день_недели][час]")
    weekdays: List[str] = Field(..., description="Названия дней недели")
    hours: List[str] = Field(..., description="Часы в формате HH:00")


class ChatMessage(BaseModel):
    id: int = Field(..., description="ID сообщения")
    user_name: str = Field(..., description="Имя пользователя")
    content: str = Field(..., description="Содержимое сообщения")
    created_at: str = Field(..., description="Время создания в ISO формате")
    created_at_formatted: str = Field(..., description="Время создания в читаемом формате")


class MessagesResponse(BaseModel):
    messages: List[ChatMessage] = Field(..., description="Список сообщений")
    total_count: int = Field(..., description="Общее количество сообщений")
    page: int = Field(..., description="Номер страницы")
    limit: int = Field(..., description="Лимит сообщений на странице")
    total_pages: int = Field(..., description="Общее количество страниц")


class AIMessage(BaseModel):
    id: int = Field(..., description="ID сообщения")
    role: str = Field(..., description="Роль (user/assistant)")
    content: str = Field(..., description="Содержимое сообщения")
    created_at: str = Field(..., description="Время создания в ISO формате")
    created_at_formatted: str = Field(..., description="Время создания в читаемом формате")


class JokesStatus(BaseModel):
    enabled: bool = Field(..., description="Статус анекдотов (включены/отключены)")
    ready: bool = Field(..., description="Готовность бота")
    message: str = Field(..., description="Описание статуса")
    interval: Dict[str, Any] = Field(..., description="Интервал между анекдотами")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    enabled: bool = Field(..., description="Статус анекдотов после операции")
    message: str = Field(..., description="Сообщение о результате")


class JokesIntervalInfo(BaseModel):
    min_minutes: int = Field(..., description="Минимальный интервал в минутах")
    max_minutes: int = Field(..., description="Максимальный интервал в минутах")
    description: str = Field(..., description="Описание интервала")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesIntervalResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    min_minutes: int = Field(..., description="Минимальный интервал после операции")
    max_minutes: int = Field(..., description="Максимальный интервал после операции")
    description: str = Field(..., description="Описание результата")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class JokesIntervalRequest(BaseModel):
    min_minutes: int = Field(..., ge=1, le=300, description="Минимальный интервал в минутах (1-300)")
    max_minutes: int = Field(..., ge=1, le=300, description="Максимальный интервал в минутах (1-300)")


class JokeGeneratedResponse(BaseModel):
    success: bool = Field(..., description="Успешность операции")
    message: str = Field(..., description="Сообщение о результате")
    next_joke: Dict[str, Any] = Field(..., description="Информация о следующем анекдоте")


class MythicalEvent(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    slot_result: str = Field(..., description="Результат слот-машины")
    result_type: str = Field(..., description="Тип результата")
    rarity_level: str = Field(..., description="Уровень редкости")
    created_at: str = Field(..., description="Время события")


class BetHourlyActivity(BaseModel):
    labels: List[str] = Field(..., description="Метки времени (часы)")
    data: List[int] = Field(..., description="Количество ставок по часам")
    total_bets: int = Field(..., description="Общее количество ставок")


class LuckyUser(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    total_bets: int = Field(..., description="Общее количество ставок")
    jackpots: int = Field(..., description="Количество джекпотов")
    mythical_count: int = Field(..., description="Количество мифических событий")
    jackpot_rate: float = Field(..., description="Процент джекпотов")
    mythical_rate: float = Field(..., description="Процент мифических событий")


class UserBalanceStats(BaseModel):
    total_users: int = Field(..., description="Общее количество пользователей")
    total_balance: int = Field(..., description="Общий баланс всех пользователей")
    avg_balance: float = Field(..., description="Средний баланс")
    median_balance: int = Field(..., description="Медианный баланс")
    total_earned: int = Field(..., description="Общая сумма заработанных средств")
    total_spent: int = Field(..., description="Общая сумма потраченных средств")
    avg_earned: float = Field(..., description="Средняя сумма заработанных средств")
    avg_spent: float = Field(..., description="Средняя сумма потраченных средств")
    active_users: int = Field(..., description="Количество активных пользователей")
    rich_users_count: int = Field(..., description="Количество богатых пользователей (>10000)")
    poor_users_count: int = Field(..., description="Количество бедных пользователей (<1000)")


class TransactionStats(BaseModel):
    total_transactions: int = Field(..., description="Общее количество транзакций")
    unique_users: int = Field(..., description="Количество уникальных пользователей")
    total_volume: int = Field(..., description="Общий объем транзакций")
    positive_volume: int = Field(..., description="Объем положительных транзакций")
    negative_volume: int = Field(..., description="Объем отрицательных транзакций")
    avg_transaction: float = Field(..., description="Средний размер транзакции")
    transaction_types: Dict[str, int] = Field(..., description="Количество транзакций по типам")
    transaction_volumes: Dict[str, int] = Field(..., description="Объемы транзакций по типам")
    daily_transactions: Dict[str, int] = Field(..., description="Транзакции по дням")


class Transaction(BaseModel):
    id: int = Field(..., description="ID транзакции")
    transaction_type: str = Field(..., description="Тип транзакции")
    amount: int = Field(..., description="Сумма транзакции")
    balance_before: int = Field(..., description="Баланс до транзакции")
    balance_after: int = Field(..., description="Баланс после транзакции")
    description: Optional[str] = Field(..., description="Описание транзакции")
    created_at: str = Field(..., description="Время создания в ISO формате")
    created_at_formatted: str = Field(..., description="Время создания в читаемом формате")


class BiggestTransaction(BaseModel):
    username: Optional[str] = Field(..., description="Имя пользователя")
    amount: int = Field(..., description="Сумма транзакции")
    type: Optional[str] = Field(..., description="Тип транзакции")
    description: Optional[str] = Field(..., description="Описание транзакции")


class StreamStats(BaseModel):
    total_streams: int = Field(..., description="Общее количество стримов")
    active_streams: int = Field(..., description="Количество активных стримов")
    completed_streams: int = Field(..., description="Количество завершенных стримов")
    total_duration_minutes: int = Field(..., description="Общая длительность всех стримов в минутах")
    avg_duration_minutes: float = Field(..., description="Средняя длительность стрима в минутах")
    total_viewers: int = Field(..., description="Общее количество зрителей")
    avg_viewers: float = Field(..., description="Среднее количество зрителей на стрим")
    max_concurrent_viewers: int = Field(..., description="Максимальное количество одновременных зрителей")
    avg_concurrent_viewers: float = Field(..., description="Среднее количество одновременных зрителей")
    popular_games: Dict[str, int] = Field(..., description="Популярные игры")
    daily_streams: Dict[str, int] = Field(..., description="Стримы по дням")


class StreamInfo(BaseModel):
    id: int = Field(..., description="ID стрима")
    title: Optional[str] = Field(..., description="Название стрима")
    game_name: Optional[str] = Field(..., description="Название игры")
    started_at: str = Field(..., description="Время начала в ISO формате")
    ended_at: Optional[str] = Field(..., description="Время окончания в ISO формате")
    duration_minutes: int = Field(..., description="Длительность в минутах")
    duration_formatted: str = Field(..., description="Длительность в читаемом формате")
    total_viewers: int = Field(..., description="Общее количество зрителей")
    max_concurrent_viewers: int = Field(..., description="Максимальное количество одновременных зрителей")
    is_active: bool = Field(..., description="Активен ли стрим")
    created_at: Optional[str] = Field(..., description="Время создания в ISO формате")
    created_at_formatted: Optional[str] = Field(..., description="Время создания в читаемом формате")


class StreamHistoryResponse(BaseModel):
    streams: List[StreamInfo] = Field(..., description="Список стримов")
    total_count: int = Field(..., description="Общее количество стримов")
    page: int = Field(..., description="Номер страницы")
    limit: int = Field(..., description="Лимит стримов на странице")
    total_pages: int = Field(..., description="Общее количество страниц")


class CurrentStreamInfo(BaseModel):
    id: int = Field(..., description="ID стрима")
    title: Optional[str] = Field(..., description="Название стрима")
    game_name: Optional[str] = Field(..., description="Название игры")
    started_at: str = Field(..., description="Время начала в ISO формате")
    duration_minutes: int = Field(..., description="Длительность в минутах")
    duration_formatted: str = Field(..., description="Длительность в читаемом формате")
    total_viewers: int = Field(..., description="Общее количество зрителей")
    max_concurrent_viewers: int = Field(..., description="Максимальное количество одновременных зрителей")
    is_active: bool = Field(..., description="Активен ли стрим")
    created_at: str = Field(..., description="Время создания в ISO формате")


class ViewerSessionStats(BaseModel):
    total_sessions: int = Field(..., description="Общее количество сессий")
    unique_viewers: int = Field(..., description="Количество уникальных зрителей")
    active_sessions: int = Field(..., description="Количество активных сессий")
    total_watch_time_minutes: int = Field(..., description="Общее время просмотра в минутах")
    avg_session_duration: float = Field(..., description="Средняя длительность сессии в минутах")
    total_rewards_claimed: int = Field(..., description="Общее количество полученных наград")
    avg_rewards_per_user: float = Field(..., description="Среднее количество наград на пользователя")
    top_reward_thresholds: Dict[str, int] = Field(..., description="Популярные пороги наград")
    daily_sessions: Dict[str, int] = Field(..., description="Сессии по дням")


class ViewerTopByTime(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    total_watch_time_minutes: int = Field(..., description="Общее время просмотра в минутах")
    total_watch_time_formatted: str = Field(..., description="Общее время просмотра в читаемом формате")
    total_sessions: int = Field(..., description="Общее количество сессий")
    avg_session_duration: float = Field(..., description="Средняя длительность сессии")
    total_rewards_claimed: int = Field(..., description="Общее количество полученных наград")
    unique_rewards: int = Field(..., description="Количество уникальных наград")


class RecentReward(BaseModel):
    username: str = Field(..., description="Имя пользователя")
    reward_threshold: int = Field(..., description="Порог награды в минутах")
    claimed_at: str = Field(..., description="Время получения в ISO формате")
    claimed_at_formatted: str = Field(..., description="Время получения в читаемом формате")


class ViewerSessionRewards(BaseModel):
    total_rewards_given: int = Field(..., description="Общее количество выданных наград")
    unique_reward_recipients: int = Field(..., description="Количество уникальных получателей наград")
    reward_distribution: Dict[str, int] = Field(..., description="Распределение наград по порогам")
    recent_rewards: List[RecentReward] = Field(..., description="Недавние награды")
    avg_rewards_per_user: float = Field(..., description="Среднее количество наград на пользователя")


class ViewerHourlyActivity(BaseModel):
    labels: List[str] = Field(..., description="Метки времени (часы)")
    data: List[int] = Field(..., description="Данные активности по часам")


class DailySessionActivity(BaseModel):
    sessions: int = Field(..., description="Количество сессий")
    watch_time_minutes: int = Field(..., description="Время просмотра в минутах")
    unique_users: int = Field(..., description="Количество уникальных пользователей")


class ViewerSessionActivity(BaseModel):
    hourly_activity: ViewerHourlyActivity = Field(..., description="Активность по часам")
    daily_activity: Dict[str, DailySessionActivity] = Field(..., description="Активность по дням")
    total_sessions: int = Field(..., description="Общее количество сессий")
