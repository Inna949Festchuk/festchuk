"""
Context7 client via MCP (Model Context Protocol).

Primary path for pulling up-to-date library/framework documentation.
Speaks the MCP Streamable-HTTP protocol to the hosted Context7 MCP server
(``https://mcp.context7.com/mcp``) using the official ``mcp`` Python SDK.

Tools used:
  - ``resolve-library-id`` : library name -> Context7 library ID (ranked)
  - ``query-docs``         : library ID + query -> markdown documentation

The legacy REST client (``context7.Context7Client``) is kept as a fallback;
this client is best-effort — any failure returns ``''`` so the caller can
fall back without breaking the agent.
"""
import asyncio
import logging
import re
from typing import Optional

import httpx2
from django.conf import settings
from mcp import ClientSession
from mcp.client import streamable_http as mcp_streamable

logger = logging.getLogger(__name__)

# The resolve tool returns a ranked text list; the first entry is the best
# match. Its ID line looks like:  "Context7-compatible library ID: /django/django"
_RESOLVE_ID_RE = re.compile(r'Context7-compatible library ID:\s*([^\s]+)')
# Fallback if the label ever changes: first /org/project[/version] token.
_FALLBACK_ID_RE = re.compile(r'(/[A-Za-z0-9._-]+/[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)?)')


class Context7MCPClient:
    """MCP client over the hosted Context7 documentation server."""

    def __init__(self):
        self.api_key = getattr(settings, 'CONTEXT7_API_KEY', '')
        self.mcp_url = getattr(
            settings, 'CONTEXT7_MCP_URL', 'https://mcp.context7.com/mcp'
        ).rstrip('/')
        self.timeout = getattr(settings, 'CONTEXT7_TIMEOUT', 15)

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @staticmethod
    def _run_coro(coro, timeout: float):
        """Run an awaitable from a sync context (Django view / agent thread)."""
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # No running loop (normal sync worker path) — run directly.
            return asyncio.run(coro)
        # Already inside a running loop: hop to a worker thread so we do not
        # nest event loops.
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result(timeout=timeout)

    async def _fetch(self, topic: str, user_query: str,
                     language: Optional[str]) -> str:
        """Resolve the library then fetch docs, within a single MCP session."""
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Accept': 'application/json, text/event-stream',
        }
        async with httpx2.AsyncClient(headers=headers, timeout=float(self.timeout)) as http:
            async with mcp_streamable.streamable_http_client(
                self.mcp_url, http_client=http
            ) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()

                    resolve = await session.call_tool(
                        'resolve-library-id',
                        {'query': user_query or topic, 'libraryName': topic},
                    )
                    library_id = self._extract_library_id(self._first_text(resolve))
                    if not library_id:
                        logger.warning('Context7 MCP: no library resolved for "%s"', topic)
                        return ''

                    params = {'libraryId': library_id, 'query': user_query or topic}
                    if language:
                        params['language'] = language
                    docs = await session.call_tool('query-docs', params)
                    if getattr(docs, 'isError', False):
                        logger.warning('Context7 MCP query-docs error for %s', library_id)
                        return ''
                    return self._first_text(docs)

    @staticmethod
    def _first_text(result) -> str:
        """Pull the first text block out of a tool result (may be empty)."""
        content = getattr(result, 'content', None)
        if not content:
            return ''
        return getattr(content[0], 'text', '') or ''

    @staticmethod
    def _extract_library_id(text: str) -> Optional[str]:
        if not text:
            return None
        m = _RESOLVE_ID_RE.search(text)
        if m:
            return m.group(1).strip()
        m = _FALLBACK_ID_RE.search(text)
        return m.group(1) if m else None

    def search(self, topic: str, user_query: str = '',
               language: Optional[str] = None,
               max_tokens: int = 2000) -> str:
        """Resolve + fetch, returning a (possibly truncated) markdown snippet."""
        if not self.enabled or not topic:
            return ''
        try:
            text = self._run_coro(
                self._fetch(topic, user_query, language),
                timeout=float(self.timeout) + 15.0,
            )
        except Exception as e:
            logger.warning('Context7 MCP search failed for "%s": %s', topic, e)
            return ''
        return self._truncate(text, max_tokens)

    @staticmethod
    def _truncate(text: str, max_tokens: int) -> str:
        if not text:
            return ''
        max_chars = max_tokens * 4
        if len(text) <= max_chars:
            return text.strip()
        cut = text.rfind('\n', 0, max_chars)
        if cut == -1 or cut < max_chars * 0.8:
            cut = max_chars
        return text[:cut] + "\n\n... [документация обрезана из-за ограничения длины]"


def get_context7_mcp_client() -> Context7MCPClient:
    return Context7MCPClient()