"""
AI Agent — orchestrates chat, RAG retrieval, function calling, and memory.

The agent:
1. Loads conversation history from Redis
2. Retrieves relevant documents via RAG (pgvector)
3. Sends messages to RouterAI with tool definitions
4. Executes requested functions (get_project_likes, search_blog_posts, etc.)
5. Saves the response and updates Redis memory
"""
import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .router_ai import RouterAIClient
from .rag import RAGService
from .context7 import get_context7_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Ты — AI-ассистент на персональном сайте-портфолио разработчика Константина Фещука.
Твоя задача — помогать посетителям узнать о проектах и статьях на сайте.

Правила:
- Если вопрос о проектах или статьях — используй предоставленный контекст.
- Если контекст пуст или недостаточно информации — честно скажи, что не нашёл ответа, и предложи посмотреть сайт.
- Не выдумывай проекты или статьи, которых нет в контексте.
- Отвечай кратко и по делу, без лишних формальностей.
- Если вопрос не относится к сайту — вежливо направь на темы портфолио.
"""

# Language instruction appended to the system prompt (driven by the UI locale).
LANGUAGE_INSTRUCTIONS = {
    'ru': 'Язык ответа: отвечай строго на русском языке.',
    'en': 'Response language: respond strictly in English.',
}

# Persona anchor appended at the very end of the system prompt (driven by the
# UI locale). Fast models lose identity when the prompt lists other agents
# (switching rules, tool descriptions, Context7 docs); recency is the strongest
# lever — the last lines win.
PERSONA_ANCHORS = {
    'ru': (
        "---\nПАМЯТЬ О СЕБЕ: ты — {code_name}. Это твоя единственная роль в диалоге. "
        "Ты НЕ являешься HYPER DRIVE, NEURAL SYNC, OMNI VISION или PRIME COORDINATOR — "
        "это другие агенты, упомянутые выше только для маршрутизации. "
        "Представляй себя только как {code_name} и отвечай в этом стиле. "
        "На вопрос «кто ты?» отвечай: «Я — {code_name}»."
    ),
    'en': (
        "---\nIDENTITY RECALL: you are {code_name}. This is your only role in this dialogue. "
        "You are NOT HYPER DRIVE, NEURAL SYNC, OMNI VISION or PRIME COORDINATOR — "
        "those are other agents mentioned above only for routing purposes. "
        "Introduce yourself only as {code_name} and answer in that style. "
        "If asked who you are, answer: 'I am {code_name}'."
    ),
}

# Naming guard: stop the model from calling the whole project after a single
# module's name (e.g. "OMNI VISION ecosystem").
NAMING_RULES = {
    'ru': (
        "Правило именования: OMNI VISION, HYPER DRIVE, QUANTUM SHIELD, NEURAL SYNC — "
        "это имена агентов-модулей, а не названия проекта. "
        "Не называй весь проект «экосистемой OMNI VISION» или экосистемой любого другого модуля. "
        "Если нужно назвать весь проект целиком, говори «экосистема этого портфолио» "
        "или «портфолио Константина Фещука»."
    ),
    'en': (
        "NAMING RULE: OMNI VISION, HYPER DRIVE, QUANTUM SHIELD and NEURAL SYNC are "
        "agent module names, not the project name. "
        "Do not refer to the whole project as the 'OMNI VISION ecosystem' or any other "
        "module's ecosystem. If you must name the whole project, say 'the ecosystem of "
        "this portfolio' or 'Konstantin Feshchuk's portfolio'."
    ),
}

# Markdown formatting rules appended to every response (global assistant and
# module SKILLs). The frontend renders chat answers as GFM markdown, so the
# model should structure answers that way (same convention as the geoscan
# AI assistant).
MARKDOWN_FORMAT_INSTRUCTIONS = """
Форматирование (ответ рендерится как Markdown, GFM):
- Пиши ответы в формате Markdown: заголовки (##) для структуры, маркированные/нумерованные списки, **жирный** для ключевых значений, таблицы для сравнения вариантов и списков объектов.
- Таблица: заголовок с колонками через | и строка-разделитель после заголовка; не шире 4-5 колонок.
- Встроенный код (`имя`, `путь`) — в обратных кавычках; блоки кода ``` только при необходимости.
- Не используй HTML-теги, эмодзи-разметку и горизонтальные линии без надобности.
- Если ответ короткий (1-2 предложения) — без заголовков и таблиц.
- По умолчанию отвечай кратко (до ~150 слов). Развёрнутые таблицы, длинные списки и блоки кода — только если пользователь просит подробнее.
"""

# Context7 library topic per module slug, so the module-specific agent can pull
# fresh documentation for its own stack. A missing slug means "no Context7
# topic for this module" (the agent still answers from RAG + SKILL).
MODULE_CONTEXT7_TOPIC = {
    'hyper-drive': 'Django 5',
    'neural-sync': 'LangChain',
    'omni-vision': 'Next.js',
}

# Tool definitions for function calling
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_stats",
            "description": "Получить статистику проекта: название, описание, технологии, количество просмотров и лайков",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "ID проекта",
                    }
                },
                "required": ["project_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_projects",
            "description": "Получить список всех проектов с кратким описанием и технологиями",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_blog_posts",
            "description": "Поиск статей в блоге по ключевым словам",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_blog_post",
            "description": "Получить содержимое статьи по ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "post_id": {
                        "type": "integer",
                        "description": "ID статьи",
                    }
                },
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "activate_module",
            "description": (
                "Переключить активного агента на другой модуль. Вызывай, когда пользователь "
                "явно просит позвать/переключить специалиста («позови бекендера», "
                "«call the frontend guy») ИЛИ когда его запрос по смыслу чётко относится "
                "к зоне одного из модулей. Не вызывай на вопросы «кто ты?» и общие "
                "навигационные вопросы — их закрывает текущий агент. Не представляйся "
                "и не отвечай от лица другого модуля, пока не вызов этот инструмент "
                "и не получишь его результат. "
                "Модули: hyper-drive — бэкенд (Django, DRF, PostgreSQL, Redis, Celery, API); "
                "quantum-shield — безопасность (rate limiting, CORS, CSRF, HTTPS, 152-ФЗ); "
                "neural-sync — искусственный интеллект (RAG, pgvector, LLM, эмбеддинги, AI-агенты); "
                "omni-vision — фронтенд (Next.js, React, TypeScript, Tailwind, UI/UX, анимации)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "module_slug": {
                        "type": "string",
                        "enum": ["hyper-drive", "quantum-shield", "neural-sync", "omni-vision"],
                        "description": "Slug модуля, которого пользователь просит вызвать",
                    },
                },
                "required": ["module_slug"],
            },
        },
    },
]


def _execute_tool(name: str, arguments: dict[str, Any], lang: str = 'ru') -> str:
    """Execute a tool function and return the result as a string."""
    try:
        if name == "get_project_stats":
            from apps.projects.models import Project
            project = Project.objects.filter(pk=arguments["project_id"]).first()
            if not project:
                return json.dumps({"error": f"Проект {arguments['project_id']} не найден"})
            return json.dumps({
                "id": project.pk,
                "title": project.get_field('title', lang),
                "description": project.get_field('summary', lang),
                "technologies": project.technologies,
                "github_url": project.github_url,
                "views": project.views_count,
                "likes": project.likes_count,
            }, ensure_ascii=False)

        elif name == "list_projects":
            from apps.projects.models import Project
            projects = Project.objects.filter(visibility=Project.Visibility.PUBLIC)
            result = [
                {
                    'id': p.pk,
                    'title': p.get_field('title', lang),
                    'summary': p.get_field('summary', lang),
                    'technologies': p.technologies,
                    'github_url': p.github_url,
                }
                for p in projects
            ]
            return json.dumps(result, ensure_ascii=False)

        elif name == "search_blog_posts":
            from apps.blog.models import Post
            query = arguments["query"].lower()
            posts = Post.objects.filter(status=Post.Status.PUBLISHED)
            filtered = [
                p for p in posts
                if query in p.get_field('title', 'ru').lower()
                or query in p.get_field('title', 'en').lower()
                or query in p.get_field('excerpt', 'ru').lower()
                or query in p.get_field('excerpt', 'en').lower()
                or any(query in tag.lower() for tag in p.tags)
            ]
            return json.dumps(
                [{'id': p.pk, 'title': p.get_field('title', lang), 'excerpt': p.get_field('excerpt', lang), 'published_at': str(p.published_at)}
                 for p in filtered[:10]],
                ensure_ascii=False,
            )

        elif name == "get_blog_post":
            from apps.blog.models import Post
            post = Post.objects.filter(pk=arguments["post_id"], status=Post.Status.PUBLISHED).first()
            if not post:
                return json.dumps({"error": f"Статья {arguments['post_id']} не найдена"})
            # Truncate content to avoid token overflow
            content = post.get_field('content', lang)[:3000]
            if len(post.get_field('content', lang)) > 3000:
                content += "\n\n[...контент урезан...]"
            return json.dumps({
                "id": post.pk,
                "title": post.get_field('title', lang),
                "content": content,
                "tags": post.tags,
            }, ensure_ascii=False)

        else:
            return json.dumps({"error": f"Неизвестная функция: {name}"})

    except Exception as e:
        logger.error(f"Tool execution error ({name}): {e}")
        return json.dumps({"error": str(e)})


class AIAgent:
    """
    AI Agent with RAG, function calling, and session memory.
    """

    def __init__(self, session, lang: str = 'ru', module_slug: str = ''):
        self.session = session
        self.lang = lang if lang in LANGUAGE_INSTRUCTIONS else 'ru'
        self.client = RouterAIClient()
        self.rag = RAGService()
        self.module_slug = module_slug or None
        self.module = None
        if self.module_slug:
            from apps.ai_agent.models import AgentModule
            self.module = AgentModule.objects.filter(
                slug=self.module_slug, is_active=True
            ).first()

    def _get_history_key(self) -> str:
        return f"chat_history:{self.session.session_id}"

    def _load_history(self) -> list[dict]:
        """Load conversation history from Redis."""
        key = self._get_history_key()
        history = cache.get(key)
        if history is None:
            # Fall back to database
            from apps.ai_agent.models import ChatMessage
            messages = self.session.messages.order_by('created_at')[:settings.MAX_CHAT_HISTORY]
            history = [
                {'role': m.role, 'content': m.content}
                for m in messages
            ]
        return history

    def _save_history(self, history: list[dict]):
        """Save conversation history to Redis with TTL."""
        key = self._get_history_key()
        # Keep only the most recent N messages
        trimmed = history[-settings.MAX_CHAT_HISTORY:]
        cache.set(key, trimmed, settings.CHAT_SESSION_TTL)

    def _fetch_context7_docs(self) -> str:
        """Fresh library docs for the active module (best-effort, Redis-cached).

        Runs in parallel with RAG retrieval; the cache in Context7Client.search
        makes repeat calls (and the post-handoff rebuild) nearly free.
        """
        if not self.module:
            return ''
        topic = MODULE_CONTEXT7_TOPIC.get(self.module_slug)
        if not topic:
            return ''
        try:
            docs = get_context7_client().search(topic, context_ids=None, max_tokens=800)
            if docs:
                logger.info(
                    f"Context7: {len(docs)} chars "
                    f"(topic={topic!r}, module={self.module_slug})"
                )
            return docs or ''
        except Exception as e:
            logger.warning(f"Context7 REST lookup failed: {e}")
            return ''

    def _build_system_prompt(self, user_message: str, rag_context: str, context7_docs: str = '') -> str:
        """System prompt for the currently active persona.

        SKILL of the active module (or the global SYSTEM_PROMPT) + markdown
        rules + language, RAG context and fresh Context7 docs. Re-called
        after activate_module so the next LLM round answers as the new persona.
        """
        if self.module and self.module.system_prompt_ru:
            base_prompt = self.module.get_field('system_prompt', self.lang)
        else:
            base_prompt = SYSTEM_PROMPT

        system_prompt = base_prompt + '\n' + MARKDOWN_FORMAT_INSTRUCTIONS + '\n' + LANGUAGE_INSTRUCTIONS[self.lang]
        if rag_context:
            system_prompt += f"\n\nКонтекст с сайта (по релевантности):\n\n{rag_context}"

        # Fresh library docs (Context7 REST) are fetched in parallel with RAG
        # in process_message and passed in; cached per topic in Context7Client.
        if context7_docs:
            topic = MODULE_CONTEXT7_TOPIC.get(self.module_slug)
            system_prompt += (
                f"\n\nСвежая документация (Context7, {topic}):\n\n{context7_docs}"
            )

        # Naming guard: prevent conflating module names with the project name.
        system_prompt += "\n\n" + NAMING_RULES[self.lang]

        # Persona anchor at the very end of the prompt (see PERSONA_ANCHORS).
        if self.module:
            system_prompt += "\n\n" + PERSONA_ANCHORS[self.lang].format(
                code_name=self.module.code_name
            )
        return system_prompt

    def _activate_module(self, slug: str) -> str:
        """activate_module tool: switch the active persona mid-conversation."""
        if not slug:
            return json.dumps({'error': 'module_slug required'}, ensure_ascii=False)
        if slug == self.module_slug:
            name = self.module.code_name if self.module else slug
            return json.dumps({'status': 'already_active', 'module': name}, ensure_ascii=False)
        from apps.ai_agent.models import AgentModule
        module = AgentModule.objects.filter(slug=slug, is_active=True).first()
        if not module:
            return json.dumps({'error': f'unknown module: {slug}'}, ensure_ascii=False)
        self.module = module
        self.module_slug = slug
        logger.info(f"Agent activated module: {slug}")
        return json.dumps({
            'status': 'activated',
            'module': module.code_name,
            'instruction': (
                f'Модуль {module.code_name} активирован. Ответь пользователю '
                'от лица этого модуля — в его роли, стиле и компетенциях.'
            ),
        }, ensure_ascii=False)

    def _handoff_marker(self, prev_slug: str) -> str:
        """History-level persona reset, injected when the active module switched.

        The end-of-system-prompt anchor loses to conversation recency when the
        history already contains another agent's self-introductions
        («Я — PRIME COORDINATOR»…), so the switch must be stated inside the
        history itself, immediately before the user's new message.
        """
        from apps.ai_agent.models import AgentModule
        prev_name = prev_slug
        if prev_slug == 'prime-coordinator':
            prev_name = 'PRIME COORDINATOR'
        else:
            prev_module = AgentModule.objects.filter(slug=prev_slug).first()
            if prev_module:
                prev_name = prev_module.code_name
        name = self.module.code_name
        if self.lang == 'en':
            return (
                f"[SYSTEM AGENT SWITCH: the active agent is now {name}. "
                f"Earlier messages in this conversation may have been answered by "
                f"{prev_name} — do not continue that persona. From this message on "
                f"you are {name} and you must introduce yourself only as {name}.]"
            )
        return (
            f"[СИСТЕМНАЯ СМЕНА АГЕНТА: с этого сообщения активным агентом является "
            f"{name}. Предыдущие сообщения могли отвечать от лица {prev_name} — не "
            f"продолжайте и не повторяйте ту роль. С этого момента вы — {name}, "
            f"представляйте себя только так.]"
        )

    def _persist_active_module(self):
        """Remember which module answered this turn (drives the next handoff marker)."""
        current = self.module_slug or ''
        if self.session.active_module_slug != current:
            self.session.active_module_slug = current
            self.session.save(update_fields=['active_module_slug'])

    def process_message(self, user_message: str) -> tuple[str, int]:
        """
        Process a user message and return the AI response.

        Returns:
            (response_text, total_tokens_used)
        """
        # 1. Load history
        history = self._load_history()

        # 1b. Persona handoff: if the active module changed since the last
        #     turn, state it inside the history (recency beats the system prompt).
        prev_slug = self.session.active_module_slug or ''
        if self.module and prev_slug and prev_slug != self.module_slug and history:
            history.append({'role': 'system', 'content': self._handoff_marker(prev_slug)})

        # 2. Add current user message
        history.append({'role': 'user', 'content': user_message})

        # 3. RAG retrieval and Context7 docs in parallel — both depend only on
        #    the user message / active module; uncached Context7 adds ~2s.
        with ThreadPoolExecutor(max_workers=2) as pool:
            rag_future = pool.submit(self.rag.search_similar, user_message)
            docs_future = pool.submit(self._fetch_context7_docs)
            rag_chunks = rag_future.result()
            context7_docs = docs_future.result()
        context = self.rag.build_context(rag_chunks)

        # 4. Build messages (system prompt is re-built after activate_module
        #    so the next LLM round answers as the new persona)
        messages = [
            {'role': 'system', 'content': self._build_system_prompt(user_message, context, context7_docs)}
        ] + history

        # 6. Call LLM with tools (max 3 rounds of tool calling)
        total_tokens = 0
        max_tool_rounds = 3

        for _ in range(max_tool_rounds + 1):
            response = self.client.chat_completion_with_tools(
                messages=messages,
                tools=TOOLS,
            )

            choice = response.choices[0]
            total_tokens += response.usage.total_tokens if response.usage else 0

            # If no tool calls, we have the final answer
            if not choice.message.tool_calls:
                assistant_text = choice.message.content or ''
                history.append({'role': 'assistant', 'content': assistant_text})
                self._save_history(history)
                self._persist_active_module()
                return assistant_text, total_tokens

            # Process tool calls
            messages.append(choice.message.model_dump())

            slug_before = self.module_slug
            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                logger.info(f"Agent calling tool: {func_name}({func_args})")
                if func_name == 'activate_module':
                    result = self._activate_module(func_args.get('module_slug', ''))
                else:
                    result = _execute_tool(func_name, func_args, lang=self.lang)

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.id,
                    'content': result,
                })

            # activate_module may have swapped the persona mid-request:
            # rebuild the system prompt so the next round answers as the new module.
            if self.module_slug != slug_before:
                messages[0] = {
                    'role': 'system',
                    'content': self._build_system_prompt(
                        user_message, context, self._fetch_context7_docs()
                    ),
                }

        # If we exit the loop without a final answer, generate one
        final_messages = messages + [
            {'role': 'user', 'content': 'Сформулируй краткий ответ на основе имеющихся данных.'}
        ]
        final_text, final_tokens = self.client.chat_completion(
            messages=final_messages,
            max_tokens=500,
        )
        total_tokens += final_tokens
        history.append({'role': 'assistant', 'content': final_text})
        self._save_history(history)
        self._persist_active_module()
        return final_text, total_tokens
