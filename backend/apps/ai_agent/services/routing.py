"""Deterministic module routing for the chat (the fast layer).

Resolution order (first hit wins):
1. an explicit module code name in the message  -> that module
2. stack keywords (AgentModule.routing_keywords, admin-editable) -> best module
3. "return to the conductor" triggers («пока», «bye», «помощник»…) -> PRIME COORDINATOR
4. otherwise -> the pinned slug (empty means the global chat, which itself
   resolves to the PRIME COORDINATOR module when it exists)

The semantic layer ("call the one who knows backend architecture") lives in
the agent itself: the LLM answers as the active persona and may call the
activate_module tool to hand the dialogue to another agent mid-reply.
"""
import logging
import re

from apps.ai_agent.models import AgentModule

logger = logging.getLogger(__name__)

COORDINATOR_SLUG = 'prime-coordinator'

# "Bye / back to the assistant" phrases: end the module session and return
# the dialogue to the conductor. Code names take priority, so
# "пока, позови HYPER DRIVE" still switches to HYPER DRIVE.
GLOBAL_ASSIST_TRIGGERS = (
    r'\bпока\b',
    r'\bдо свидания\b',
    r'\bвыход\b',
    r'\bbye\b',
    r'\bgoodbye\b',
    r'neural[- ]?assist',
    r'нейро-?ассистент',
    r'\bпомощник\w*',
    r'\bassistant\b',
)

# Fallback keyword lists when the DB field is empty. Stems are matched with a
# leading word boundary ("бэкенд" also hits "бэкендер", "бэкенде"); keywords
# of 3 characters or less are matched as whole words ("AI", "БД", "UI").
DEFAULT_ROUTING_KEYWORDS = {
    'hyper-drive': (
        'бэкенд', 'бекенд', 'бэкэнд', 'backend', 'django', 'drf', 'rest api',
        'postgresql', 'postgres', 'база данных', 'базы данных', 'бд',
        'redis', 'celery', 'сервер', 'серверн', 'миграци', 'эндпоинт',
    ),
    'quantum-shield': (
        'безопасн', 'security', 'защит', 'уязвимост', 'rate limit',
        'троттлинг', 'throttl', 'cors', 'csrf', 'https', 'ssl', '152-фз',
        'персональн', 'анонимн', 'авторизац', 'аутентификац', 'ddos',
    ),
    'neural-sync': (
        'искусственн', 'нейросет', 'rag', 'вектор',
        'эмбеддинг', 'embedding', 'llm', 'gpt', 'qwen', 'промпт', 'prompt',
        'машинн обучен', 'ml', 'context7', 'function calling',
    ),
    'omni-vision': (
        'фронтенд', 'frontend', 'react', 'next.js', 'typescript', 'ui',
        'ux', 'интерфейс', 'вёрстка', 'верстка', 'tailwind',
        'css', 'html', 'анимаци', 'framer', 'адаптив', 'дизайн',
        'компонент',
    ),
}


def _parse_keywords(text: str) -> list[str]:
    return [part.strip() for part in re.split(r'[,;\n]+', text or '') if part.strip()]


def _keyword_score(message: str, keywords) -> tuple[int, int]:
    """Return (hits, longest_hit_length) for a keyword list."""
    hits = 0
    longest = 0
    for kw in keywords:
        kw = kw.lower()
        if len(kw) <= 3:
            pattern = rf'\b{re.escape(kw)}\b'
        else:
            pattern = rf'\b{re.escape(kw)}'
        if re.search(pattern, message, re.IGNORECASE):
            hits += 1
            longest = max(longest, len(kw))
    return hits, longest


def _coordinator_or_empty() -> str:
    """Empty chat resolves to the PRIME COORDINATOR module when it exists."""
    if AgentModule.objects.filter(slug=COORDINATOR_SLUG, is_active=True).exists():
        return COORDINATOR_SLUG
    return ''


def resolve_module_slug(user_message: str, pinned_slug: str = '') -> str:
    """Deterministic layer of module routing (see module docstring)."""
    modules = list(
        AgentModule.objects.filter(is_active=True)
        .values_list('code_name', 'slug', 'routing_keywords')
    )

    # 1. Explicit code name (longest first so "PRIME COORDINATOR" wins over
    #    shorter names when both appear).
    for code_name, slug, _ in sorted(modules, key=lambda m: len(m[0]), reverse=True):
        if code_name and re.search(re.escape(code_name), user_message, re.IGNORECASE):
            return slug

    # 2. Stack keywords; ties broken by the longer matched keyword, then by
    #    slug order (deterministic).
    best_slug = ''
    best_score = (0, 0)
    for code_name, slug, kw_text in sorted(modules, key=lambda m: m[1]):
        keywords = _parse_keywords(kw_text) or DEFAULT_ROUTING_KEYWORDS.get(slug, ())
        score = _keyword_score(user_message, keywords)
        if score[0] and score > best_score:
            best_slug, best_score = slug, score
    if best_slug:
        return best_slug

    # 3. "Back to the conductor" triggers.
    for pattern in GLOBAL_ASSIST_TRIGGERS:
        if re.search(pattern, user_message, re.IGNORECASE):
            return _coordinator_or_empty()

    # 4. Keep the pinned module (or fall back to the coordinator for the
    #    empty/global chat).
    return pinned_slug or _coordinator_or_empty()
