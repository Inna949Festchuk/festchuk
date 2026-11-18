"""
Context7 client — pulls up-to-date library/framework documentation.

Talks to the Context7 HTTP API. Used to give the AI agent fresh,
authoritative reference material when answering technical questions.

The integration is best-effort: any failure is swallowed and returns 
None/empty string so the agent falls back to its RAG-only context.
"""
import logging
from typing import Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class Context7Client:
    """Thin client over the Context7 documentation API."""

    def __init__(self):
        self.api_key = getattr(settings, 'CONTEXT7_API_KEY', '')
        self.base_url = getattr(
            settings, 'CONTEXT7_BASE_URL', 'https://context7.com/api/v1'
        ).rstrip('/')
        
        # Используем кортеж (connect_timeout, read_timeout)
        timeout_val = getattr(settings, 'CONTEXT7_TIMEOUT', 8)
        self.timeout = (3, timeout_val) if isinstance(timeout_val, (int, float)) else timeout_val
        
        # Сессия для переиспользования TCP-соединений (keep-alive)
        self._session = requests.Session()

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    def _headers(self) -> dict:
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json',
        }

    def resolve_context_id(self, title: str) -> Optional[str]:
        """Resolve a library/framework title to a Context7 library ID.

        Real v1 API (verified live 2026-11-09): GET /api/v1/search?query=...
        returns {"results": [{"id": "/vercel/next.js", "title": ..., ...}]}.
        The legacy /tokens/resolve path does not exist (404).
        """
        if not self.enabled or not title:
            return None
        try:
            resp = self._session.get(
                f'{self.base_url}/search',
                params={'query': title},
                headers=self._headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            results = data.get('results') or []
            if not results:
                return None
            return results[0].get('id') or None
        except Exception as e:
            # exc_info=True добавит traceback в логи сервера, но не сломает агент
            logger.warning(f'Context7 search failed for "{title}": {e}', exc_info=True)
            return None

    def fetch_documentation(self, context_id: str, topic: Optional[str] = None,
                            tokens: int = 2000) -> Optional[str]:
        """Fetch documentation markdown for a library ID.

        Real v1 API: GET /api/v1/{owner}/{repo}?type=txt&topic=...&tokens=N
        (library ID without the leading slash) -> plain-text markdown, not JSON.
        """
        if not self.enabled or not context_id:
            return None
        try:
            path = context_id.lstrip('/')
            params = {'type': 'txt', 'tokens': tokens}
            if topic:
                params['topic'] = topic

            resp = self._session.get(
                f'{self.base_url}/{path}',
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            return resp.text
        except Exception as e:
            logger.warning(f'Context7 documentation fetch failed for {context_id}: {e}', exc_info=True)
            return None

    def search(self, topic: str, context_ids: Optional[list[str]] = None,
               max_tokens: int = 2000) -> str:
        """Search documentation and return a concatenated markdown snippet."""
        if not self.enabled or not topic:
            return ''

        # Доки библиотек меняются редко: кэш убирает ~2с REST-запроса из
        # каждого сообщения модуля (и повторного после activate_module).
        # Пустой результат кэшируем на 5 минут — чтобы не долбить лежащий API.
        cache_key = f'context7:docs:{topic}:{max_tokens}:{",".join(context_ids or [])}'
        cached = cache.get(cache_key)
        if cached is not None:
            logger.info(f'Context7: cache hit (topic={topic!r}, {len(cached)} chars)')
            return cached

        ids = list(context_ids or [])
        if not ids:
            context_id = self.resolve_context_id(topic)
            if context_id:
                ids = [context_id]

        chunks = []
        # Ограничиваем количество запросов, чтобы не перегружать API и не ждать долго
        for context_id in ids[:3]:
            doc = self.fetch_documentation(context_id, topic=topic, tokens=max_tokens)
            if doc:
                chunks.append(doc)

        text = '\n\n'.join(chunks).strip()

        if text and max_tokens:
            max_chars = max_tokens * 4
            if len(text) > max_chars:
                # Умная обрезка: ищем последний перенос строки перед лимитом,
                # чтобы не разрывать markdown-блоки или слова посередине.
                cut_idx = text.rfind('\n', 0, max_chars)
                if cut_idx == -1 or cut_idx < max_chars * 0.8:
                    cut_idx = max_chars # Фоллбек, если переносов строки нет

                text = text[:cut_idx] + "\n\n... [документация обрезана из-за ограничения длины]"

        ttl = getattr(settings, 'CONTEXT7_CACHE_TTL', 21600)
        cache.set(cache_key, text, ttl if text else 300)
        return text

    def __del__(self):
        # Хорошая практика: закрывать сессию при уничтожении объекта
        if hasattr(self, '_session'):
            self._session.close()


def get_context7_client() -> Context7Client:
    return Context7Client()