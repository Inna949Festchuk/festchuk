"""
Тесты суточного бюджета LLM (services/budget.py).

Используют дефолтный кэш (Redis контейнера) — ключи чистятся ТОЧЕЧНО по
текущей UTC-дате, не cache.clear() (dev-Redis общий на весь сайт).
БД не требуется: счётчики живут только в кэше.
"""
import pytest

from django.core.cache import cache

from apps.ai_agent.services import budget
from apps.ai_agent.services.budget import (
    DailyBudgetExceeded,
    check_daily_budget,
    claim_request,
    record_tokens,
)


@pytest.fixture(autouse=True)
def clean_budget_keys():
    """Обнулить счётчики дня до и после каждого теста (точечно по ключам)."""
    for kind in ('requests', 'tokens'):
        cache.delete(budget._key(kind))
    yield
    for kind in ('requests', 'tokens'):
        cache.delete(budget._key(kind))


def test_check_passes_when_counters_absent(settings):
    settings.ROUTERAI_DAILY_MAX_REQUESTS = 100
    settings.ROUTERAI_DAILY_MAX_TOKENS = 1000

    check_daily_budget()  # не должно падать


def test_claim_and_record_increment_counters(settings):
    settings.ROUTERAI_DAILY_MAX_REQUESTS = 100
    settings.ROUTERAI_DAILY_MAX_TOKENS = 1000

    claim_request()
    record_tokens(500)

    assert cache.get(budget._key('requests')) == 1
    assert cache.get(budget._key('tokens')) == 500
    check_daily_budget()


def test_check_raises_on_request_limit(settings):
    settings.ROUTERAI_DAILY_MAX_REQUESTS = 3
    settings.ROUTERAI_DAILY_MAX_TOKENS = 100000

    for _ in range(3):
        claim_request()

    with pytest.raises(DailyBudgetExceeded) as exc_info:
        check_daily_budget()
    assert exc_info.value.kind == 'requests'


def test_check_raises_on_token_limit(settings):
    settings.ROUTERAI_DAILY_MAX_REQUESTS = 100
    settings.ROUTERAI_DAILY_MAX_TOKENS = 1000

    record_tokens(600)
    check_daily_budget()  # 600 < 1000 — ещё в норме
    record_tokens(500)  # 1100 ≥ 1000

    with pytest.raises(DailyBudgetExceeded) as exc_info:
        check_daily_budget()
    assert exc_info.value.kind == 'tokens'


def test_record_tokens_zero_is_noop(settings):
    settings.ROUTERAI_DAILY_MAX_REQUESTS = 100
    settings.ROUTERAI_DAILY_MAX_TOKENS = 1000

    record_tokens(0)

    assert cache.get(budget._key('tokens')) is None
