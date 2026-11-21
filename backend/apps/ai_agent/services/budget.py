"""
Суточный бюджет LLM (circuit breaker на расходе RouterAI).

Троттлинг per-IP (30/ч на чат) защищает от одиночного спама, но не от
распределённой волны (разные IP после публикации на Хабре) — она быстро
сливает баланс. Здесь — глобальные счётчики в Redis:

- stats:routerai:daily:{UTC-дата}:requests — число chat-запросов за день;
- stats:routerai:daily:{UTC-дата}:tokens   — сумма total_tokens за день.

Счётчики живут 48ч (один день + запас), дальше удаляются самим Redis.
"""
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache

_BUDGET_KEY_TTL = 48 * 3600


class DailyBudgetExceeded(Exception):
    """Дневной лимит запросов или токенов исчерпан."""

    def __init__(self, kind: str):
        self.kind = kind  # 'requests' | 'tokens'
        super().__init__(f'daily {kind} budget exceeded')


def _key(kind: str) -> str:
    date = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    return f'stats:routerai:daily:{date}:{kind}'


def _counter(kind: str) -> int:
    """Текущее значение счётчика (0, если ключ ещё не создан)."""
    value = cache.get(_key(kind))
    return int(value) if value is not None else 0


def _incr(kind: str, amount: int = 1) -> None:
    # cache.add — атомарный SETNX: создаём ключ нулём, если его нет.
    # Гонка «два add» безвредна: счётчик лишь сбросится в начало дня,
    # что допустимо для предохранительного предела.
    cache.add(_key(kind), 0, _BUDGET_KEY_TTL)
    try:
        cache.incr(_key(kind), amount)
    except ValueError:
        # Ключ исчез между add и incr (TTL/вытеснение) — повторяем.
        cache.add(_key(kind), 0, _BUDGET_KEY_TTL)
        cache.incr(_key(kind), amount)


def check_daily_budget() -> None:
    """Поднять DailyBudgetExceeded, если дневной лимит уже исчерпан."""
    if _counter('requests') >= settings.ROUTERAI_DAILY_MAX_REQUESTS:
        raise DailyBudgetExceeded('requests')
    if _counter('tokens') >= settings.ROUTERAI_DAILY_MAX_TOKENS:
        raise DailyBudgetExceeded('tokens')


def claim_request() -> None:
    """Зарезервировать один chat-запрос (до LLM-вызова)."""
    _incr('requests')


def record_tokens(total_tokens: int) -> None:
    """Учесть токены завершённого хода (usage из финального ответа)."""
    if total_tokens > 0:
        _incr('tokens', total_tokens)
