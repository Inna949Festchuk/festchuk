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
        """Resolve a library/framework title to a Context7 context id."""
        if not self.enabled or not title:
            return None
        try:
            resp = self._session.get(
                f'{self.base_url}/tokens/resolve',
                params={'title': title},
                headers=self._headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get('contextId') or data.get('context_id')
        except Exception as e:
            # exc_info=True добавит traceback в логи сервера, но не сломает агент
            logger.warning(f'Context7 resolve failed for "{title}": {e}', exc_info=True)
            return None

    def fetch_documentation(self, context_id: str, topic: Optional[str] = None) -> Optional[str]:
        """Fetch documentation markdown for a context id, optionally on a topic."""
        if not self.enabled or not context_id:
            return None
        try:
            params = {}
            if topic:
                params['topic'] = topic
                
            resp = self._session.get(
                f'{self.base_url}/documentation/{context_id}',
                params=params,
                headers=self._headers(),
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            
            for key in ('markdown', 'documentation', 'content', 'text'):
                if data.get(key):
                    return str(data[key])
            return None
        except Exception as e:
            logger.warning(f'Context7 documentation fetch failed for {context_id}: {e}', exc_info=True)
            return None

    def search(self, topic: str, context_ids: Optional[list[str]] = None,
               max_tokens: int = 2000) -> str:
        """Search documentation and return a concatenated markdown snippet."""
        if not self.enabled or not topic:
            return ''

        ids = list(context_ids or [])
        if not ids:
            context_id = self.resolve_context_id(topic)
            if context_id:
                ids = [context_id]

        chunks = []
        # Ограничиваем количество запросов, чтобы не перегружать API и не ждать долго
        for context_id in ids[:3]:
            doc = self.fetch_documentation(context_id, topic=topic)
            if doc:
                chunks.append(doc)

        text = '\n\n'.join(chunks).strip()
        if not text:
            return ''
            
        if max_tokens:
            max_chars = max_tokens * 4
            if len(text) > max_chars:
                # Умная обрезка: ищем последний перенос строки перед лимитом,
                # чтобы не разрывать markdown-блоки или слова посередине.
                cut_idx = text.rfind('\n', 0, max_chars)
                if cut_idx == -1 or cut_idx < max_chars * 0.8:
                    cut_idx = max_chars # Фоллбек, если переносов строки нет
                
                text = text[:cut_idx] + "\n\n... [документация обрезана из-за ограничения длины]"
                
        return text

    def __del__(self):
        # Хорошая практика: закрывать сессию при уничтожении объекта
        if hasattr(self, '_session'):
            self._session.close()


def get_context7_client() -> Context7Client:
    return Context7Client()