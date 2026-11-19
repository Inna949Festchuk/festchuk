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
# The language is pinned: user messages may arrive in another language (voice
# transcription glitches, EN quick phrases) — the reply must not follow them.
# Full foreign-language sentences are banned outright: the model kept finishing
# a thought in English right after an English name/term ("…LangChain. As
# mentioned above, the pipeline…" — 2026-11-19), so the rule names the exact
# failure pattern, not just the target language.
LANGUAGE_INSTRUCTIONS = {
    'ru': (
        'Язык ответа: отвечай строго на русском языке. Язык ответа закреплён: '
        'не переключайся на язык сообщения пользователя — если пользователь пишет '
        'по-английски или на другом языке (в том числе из-за ошибок распознавания '
        'голоса), всё равно отвечай по-русски. Англоязычные вкрапления — только '
        'названия, термины, аббревиатуры и код, встроенные в русские предложения; '
        'сразу после английского слова продолжай фразу по-русски. Полностью '
        'английские предложения, обороты и связки («as mentioned above», '
        '«in summary», «let me explain» и т. п.) в ответе запрещены — заменяй '
        'их русскими.'
    ),
    'en': (
        "Response language: respond strictly in English. The language is pinned: "
        "do not switch to the user's message language — if the user writes in Russian "
        "or another language (including voice-transcription glitches), still reply in "
        "English. Non-English insertions are allowed only as names, terms, "
        "abbreviations and code embedded in English sentences; immediately after a "
        "foreign word continue the sentence in English. Full sentences, phrases or "
        "connectives in another language are forbidden."
    ),
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

# Data guard: fast models complete lists from imagination when RAG shows only
# a couple of real titles («Какие статьи?» → 10 выдуманных постов, 2026-11-18).
# The first version allowed «или из контекста» — with partial RAG data the
# model skipped list_projects and claimed a fire project didn't exist.
# Composition/existence claims now require tools; context is details only.
# Lives in code (not in Admin SKILLs) so it applies to every persona — the
# global SYSTEM_PROMPT with its «не выдумывай» rule is NOT used when a module
# SKILL exists.
DATA_RULES = {
    'ru': (
        "Правило данных: наличие, отсутствие и полные списки проектов и статей подтверждай "
        "ТОЛЬКО инструментами (list_projects, list_blog_posts, search_blog_posts, get_blog_post). "
        "Контекст выше — источник деталей и цитат, но НЕ основание для выводов о составе: "
        "в нём могут быть лишь отдельные записи. Перед любым сопоставлением, сравнением или "
        "поиском соответствий между проектами и статьями получи оба списка инструментами. "
        "Если инструмент вернул пусто — честно скажи, что не нашёл. "
        "НИКОГДА не выдумывай названия, ID или описания. "
        "Не оформляй названия ссылками без реального URL."
    ),
    'en': (
        "DATA RULE: confirm the presence, absence and full lists of projects and articles "
        "ONLY with the tools (list_projects, list_blog_posts, search_blog_posts, get_blog_post). "
        "The context above is a source of details and quotes, NOT grounds for conclusions "
        "about what exists: it may contain only individual records. Before any matching, "
        "comparison or cross-referencing of projects and articles, fetch both lists with the tools. "
        "If a tool returns empty, say honestly that you found nothing. "
        "NEVER invent names, IDs or descriptions. "
        "Do not format names as links without a real URL."
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
- Перед ЛЮБОЙ таблицей обязательно — одно-два предложения, резюмирующие её СОДЕРЖАНИЕ: какие строки/категории в ней и главный вывод, и назови темы строк. Пример: «В таблице — четыре направления: GeoAI и спутниковый мониторинг, AI-агенты и LLM, веб-разработка, автоматизация; у каждого есть флагманский проект». Не общие фразы («в таблице результаты») — назови темы строк. Озвучка читает только это пояснение, не ячейки таблицы. Таблицы пиши ТОЛЬКО через символ |; табличные строки через табуляцию запрещены.
- Встроенный код (`имя`, `путь`) — в обратных кавычках; блоки кода ``` только при необходимости.
- Не используй HTML-теги, эмодзи-разметку и горизонтальные линии без надобности.
- Если ответ короткий (1-2 предложения) — без заголовков и таблиц.
- По умолчанию отвечай кратко (до ~150 слов). Развёрнутые таблицы, длинные списки и блоки кода — только если пользователь просит подробнее.
- Начинай сразу с сути: первое предложение — результат или пояснение к таблице. Не начинай ответ с анонса собственных действий («теперь сопоставлю», «сейчас разберу», «я проанализировал», «получил списки», «давай посмотрим» — в любых словоформах и порядке слов).
- Не показывай внутренние ID проектов и статей в тексте ответа (даже если в предыдущих сообщениях диалога они встречались) — они нужны только для вызова инструментов. Называй записи по заголовку/названию.
- Не повторяй название проекта или статьи несколько раз в одном ответе: назови один раз, дальше — по теме («первый проект», «статья про спутниковые снимки»). Ответ будет озвучен голосом: пиши цельным языком диалога, англоязычные вкрапления — только названия, аббревиатуры и термины; не цитируй описания проектов на английском — пересказывай по-русски. Англоязычный термин ставь в середине предложения, а не в начале: не «RAG: фреймворк упрощает…», а «векторный поиск (RAG) упрощает…» — иначе озвучка переключает фрагмент на английский. Это правило действует и для КАЖДОГО пункта списка — пункт списка это то же предложение: не начинай его с английского названия или термина, сначала русская формулировка, английское — в скобках или в середине: не «SSR/ISR — SEO для блога», а «серверный рендеринг (SSR/ISR) — SEO для блога»; не «TypeScript — строгая типизация», а «строгая типизация (TypeScript)»; не «Tailwind + Framer Motion — неоновая эстетика», а «неоновая эстетика (Tailwind + Framer Motion)». Это касается и названий категорий/уровней в списках: не «Per-view — декоратор…», а «кэш уровня view (per-view) — декоратор…». Не переходи на английский внутри мысли: после английского названия или термина продолжай предложение по-русски, полностью английские предложения и связки (даже одно) запрещены.
"""

# Short style restatement placed right before the persona anchor: the key
# user-visible rules repeated at the end of the system prompt are followed
# more reliably than the same rules buried in the markdown block above
# (preamble «теперь сопоставлю…» recurred despite the earlier rule).
STYLE_RULES = {
    'ru': (
        "Стиль ответа: первое предложение — сразу результат или пояснение к таблице. "
        "Никогда не начинай с анонса собственных действий («теперь сопоставлю», «я "
        "проанализировал», «сейчас разберу» и любые другие формулировки этого рода), "
        "в том числе деепричастиями о собственной работе: не «Проанализировав список, "
        "выделяю…», а «В портфолио четыре основных направления: …». "
        "Внутренние ID записей в ответе не показывай. "
        "Ни одно предложение и ни один пункт списка не начинай с английского слова: "
        "сначала русская формулировка, английское название или термин — в скобках "
        "или в середине («строгая типизация (TypeScript)», а не «TypeScript — "
        "строгая типизация»). Названия категорий и уровней в списках — тоже: "
        "не «Per-view — декоратор…», а «кэш уровня view (per-view) — декоратор…»; "
        "не «Low-level API — …», а «низкоуровневый API (low-level) — …» — "
        "иначе озвучка переключает фрагмент на английский."
    ),
    'en': (
        "Reply style: the first sentence is the result or the table explanation, never an "
        "announcement of your own actions («let me now…», «I analyzed…», «Having analyzed "
        "the list, I highlight…» and the like). "
        "Do not show internal record IDs in the answer. "
        "Never start a sentence or a list item with a word in another language: lead "
        "with English and put non-English names and terms in parentheses or mid-sentence."
    ),
}

# Context7 library topic per module slug: fresh docs for the module's own
# stack, auto-injected into its prompt every turn. The mapping is
# configuration, not code — settings.CONTEXT7_MODULE_TOPICS, env-overridable
# via the CONTEXT7_MODULE_TOPICS JSON. A missing slug means "no Context7
# topic for this module" (the agent still answers from RAG + SKILL).
MODULE_CONTEXT7_TOPIC = dict(getattr(settings, 'CONTEXT7_MODULE_TOPICS', None) or {})

# Context7 self-awareness. The SKILLs name Context7 as a capability, but the
# model cannot find it in TOOLS — so agents answered «no direct access to
# Context7, only portfolio tools» while auto-injected docs sat right in their
# own prompt (incident 2026-11-19: NEURAL SYNC denied Context7 access). The
# actual access mode is dynamic (topic per module, best-effort fetch), so it
# is stated here in code, per turn, for every persona — not in the SKILLs.
CONTEXT7_AWARENESS = {
    'ru': {
        'connected': (
            "Context7: ты подключён к актуальной документации по теме «{topic}» — "
            "блок «Свежая документация (Context7, …)» подгружается в твой промпт "
            "автоматически, каждый ход, без просьбы пользователя. Опирайся на неё "
            "ОБЯЗАТЕЛЬНО и в первую очередь на ЛЮБОЙ вопрос по твоему стеку — "
            "«как сделать», «как улучшить проект», «актуально ли X», «правильно ли "
            "подобрано», «есть ли свежий способ» — даже если пользователь не "
            "упоминает Context7. Если документация противоречит твоей внутренней "
            "памяти — доверься документации, она свежее. Приоритет источников: "
            "общие технические вопросы («как правильно настроить», «как вообще», "
            "best practices) закрывай связкой Context7 + память — сначала "
            "документация, твоя память дополняет то, чего в доках нет; не отвечай "
            "из одной памяти, пока доки подгружены и релевантны. RAG-контекст — "
            "ТОЛЬКО для вопросов о том, как устроено и настроено в этом портфолио, "
            "не для общих best practices. Если вопрос касается библиотеки, которой "
            "нет в твоём автоматическом контексте (CORS → django-cors-headers, "
            "rate limiting → Django REST Framework, кэш → Django), — вызови "
            "инструмент fetch_context7_docs с названием библиотеки и опирайся на "
            "полученные доки. Для темы «{topic}» инструмент не вызывай — она уже "
            "в промпте. Если "
            "пользователь просит «подключиться к Context7» или «использовать "
            "Context7» — не говори, что доступа нет: документация по теме «{topic}» "
            "уже в твоём контексте, объясни это и ответь, опираясь на неё. Не "
            "выдавай документацию библиотек за новости индустрии."
        ),
        'unavailable': (
            "Context7: у твоей роли есть тема документации «{topic}», но в этом "
            "промпте свежая документация НЕ подгружена — источник временно "
            "недоступен. Не заявляй, что подключён к Context7 автоматически. "
            "Ты можешь запросить доки нужной библиотеки инструментом "
            "fetch_context7_docs; если документация не получена — честно скажи, "
            "что свежая документация недоступна, и ответь из памяти. Приоритет "
            "источников: общие технические вопросы — Context7 (через инструмент) "
            "+ твоя память; RAG-контекст — только для вопросов о том, как "
            "устроено и настроено в этом портфолио."
        ),
        'no_access': (
            "Context7: к твоей роли свежая документация автоматически НЕ "
            "подгружается. Но ты можешь запросить доки конкретной библиотеки "
            "инструментом fetch_context7_docs (тема — название библиотеки). "
            "Если пользователь просит «подключиться к Context7» — объясни: "
            "автоматических доков у твоей роли нет, но по запросу ты получишь "
            "доки нужной библиотеки; при необходимости предложи модуль, который "
            "закрывает тему (NEURAL SYNC — AI/LLM, HYPER DRIVE — бэкенд, "
            "OMNI VISION — фронтенд). Приоритет источников: общие технические "
            "вопросы — Context7 (через инструмент) + твоя память; RAG-контекст — "
            "только для вопросов о том, как устроено и настроено в этом портфолио."
        ),
    },
    'en': {
        'connected': (
            "Context7: you are connected to up-to-date documentation for the topic "
            "'{topic}' — the documentation block is injected into your prompt "
            "automatically, every turn, without the user asking. You MUST rely on it "
            "first for ANY question about your stack — 'how to do it', 'how to "
            "improve the project', 'is X up to date', 'is the framework the right "
            "choice', 'is there a newer way' — even when the user never mentions "
            "Context7. When the documentation conflicts with your internal "
            "knowledge, trust the documentation: it is newer. Source priority: "
            "general technical questions ('how to configure it correctly', 'how "
            "does it work in general', best practices) are answered with Context7 "
            "+ your own knowledge — documentation first, your knowledge supplements "
            "what the docs do not cover; do not answer from knowledge alone while "
            "relevant docs are injected. The RAG context is ONLY for questions "
            "about how things are built and configured in this portfolio, not for "
            "general best practices. If the question concerns a library that is "
            "not in your automatic context (CORS → django-cors-headers, rate "
            "limiting → Django REST Framework, caching → Django), call the "
            "fetch_context7_docs tool with the library name and rely on the "
            "returned docs. Do not call it for '{topic}' — it is already in your "
            "prompt. If the user asks you to "
            "'connect to Context7' or 'use Context7' — do not say you have no "
            "access: the documentation for '{topic}' is already in your context; "
            "explain that and answer based on it. Do not present library "
            "documentation as industry news."
        ),
        'unavailable': (
            "Context7: your role has a documentation topic ('{topic}'), but no "
            "fresh documentation was injected into this prompt — the source is "
            "temporarily unavailable. Do not claim you are connected to Context7 "
            "automatically. You can request docs for the needed library with the "
            "fetch_context7_docs tool; if no documentation is returned, say "
            "honestly that fresh documentation is unavailable and answer from "
            "your knowledge. Source priority: general technical questions — "
            "Context7 (via the tool) + your own knowledge; the RAG context — "
            "only for questions about how things are built and configured in "
            "this portfolio."
        ),
        'no_access': (
            "Context7: no fresh documentation is injected for your role "
            "automatically. However, you can request docs for a specific library "
            "with the fetch_context7_docs tool (topic = library name). If the "
            "user asks you to 'connect to Context7', explain: your role has no "
            "automatic docs, but you can fetch docs for any library on request; "
            "when relevant, suggest the module that covers the topic (NEURAL "
            "SYNC — AI/LLM, HYPER DRIVE — backend, OMNI VISION — frontend). "
            "Source priority: general technical questions — Context7 (via the "
            "tool) + your own knowledge; the RAG context — only for questions "
            "about how things are built and configured in this portfolio."
        ),
    },
}

# Verified stack facts injected into every persona's prompt: agents kept
# inventing stack details from internal memory when Context7 docs did not
# cover the topic (2026-11-19: neural-sync called the TTS «tts-1-hd» instead
# of gemini-tts; hyper-drive denied Django's built-in Redis cache backend and
# recommended django-redis). AI-config lines are built from settings at
# prompt-build time (see AIAgent._stack_facts) so they never drift from .env.
STACK_FACTS = {
    'ru': (
        "Факты о стеке этого портфолио (проверены и актуальны; они приоритетнее "
        "твоей внутренней памяти — не выдумывай названия моделей, библиотек и версий):\n"
        "- Backend: Python 3.12, Django 5.0 + DRF, Celery + django-celery-beat, "
        "Channels/Daphne, gunicorn в prod.\n"
        "- База данных: PostgreSQL 15 + pgvector.\n"
        "- Redis 7: кэш — DB0, брокер Celery — DB1, результаты задач — DB2. "
        "Кэш работает на встроенном бэкенде Django "
        "`django.core.cache.backends.redis.RedisCache` (Django 4.0+), "
        "сторонний django-redis НЕ используется.\n"
        "- Frontend: Next.js 14.2 (App Router, standalone), React 18, TypeScript, "
        "Tailwind CSS, Framer Motion, next-intl (RU/EN), react-markdown + remark-gfm "
        "+ rehype-highlight, axios; display-шрифт Geologica (self-hosted).\n"
        "- Инфраструктура: Docker Compose (dev/prod), Nginx в prod "
        "(reverse proxy, rate limiting, static/media).\n"
        "- AI-провайдер: RouterAI — OpenAI-совместимый API (routerai.ru/api/v1).\n"
        "{ai_facts}"
        "- Context7: REST v1 (context7.com/api/v1); свежая документация "
        "подгружается в промпт автоматически по теме модуля, инструмент "
        "fetch_context7_docs запрашивает доки произвольной библиотеки по требованию.\n"
        "Эти факты описывают данный проект. Для общих технических вопросов "
        "действует приоритет источников (Context7 + память). Если факта нет ни "
        "здесь, ни в документации — честно скажи, что не знаешь, не выдумывай."
    ),
    'en': (
        "Verified facts about this portfolio's stack (current; they take priority "
        "over your internal knowledge — do not invent model names, libraries or "
        "versions):\n"
        "- Backend: Python 3.12, Django 5.0 + DRF, Celery + django-celery-beat, "
        "Channels/Daphne, gunicorn in prod.\n"
        "- Database: PostgreSQL 15 + pgvector.\n"
        "- Redis 7: cache — DB0, Celery broker — DB1, task results — DB2. "
        "Caching uses Django's built-in backend "
        "`django.core.cache.backends.redis.RedisCache` (Django 4.0+); "
        "the third-party django-redis is NOT used.\n"
        "- Frontend: Next.js 14.2 (App Router, standalone), React 18, TypeScript, "
        "Tailwind CSS, Framer Motion, next-intl (RU/EN), react-markdown + remark-gfm "
        "+ rehype-highlight, axios; display font Geologica (self-hosted).\n"
        "- Infrastructure: Docker Compose (dev/prod), Nginx in prod "
        "(reverse proxy, rate limiting, static/media).\n"
        "- AI provider: RouterAI — an OpenAI-compatible API (routerai.ru/api/v1).\n"
        "{ai_facts}"
        "- Context7: REST v1 (context7.com/api/v1); fresh documentation is "
        "injected into the prompt automatically per module topic; the "
        "fetch_context7_docs tool fetches docs for any library on demand.\n"
        "These facts describe this project. General technical questions follow "
        "the source priority (Context7 + your knowledge). If a fact is neither "
        "here nor in the documentation, say honestly that you do not know — "
        "do not invent it."
    ),
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
            "description": "Поиск статей в блоге по ключевым словам. Пустой или отсутствующий query возвращает все статьи.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Поисковый запрос (необязательно)",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_blog_posts",
            "description": (
                "Получить список ВСЕХ статей блога: id, заголовок, краткое описание, дата. "
                "Вызывай для вопросов «какие статьи есть в блоге» и любых списков статей — "
                "не составляй список из головы."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
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
    {
        "type": "function",
        "function": {
            "name": "fetch_context7_docs",
            "description": (
                "Получить свежую документацию библиотеки или фреймворка из Context7 "
                "по произвольной теме. Вызывай, когда вопрос касается конкретной "
                "библиотеки, которой нет в блоке «Свежая документация» твоего промпта "
                "(например: CORS → django-cors-headers, rate limiting/throttling → "
                "Django REST Framework, кэширование → Django, очереди → Celery). "
                "topic — название библиотеки/фреймворка, а не вопрос целиком. "
                "Не вызывай для темы, уже подгруженной в промпт, и для вопросов о "
                "проектах/статьях портфолио (для них — list_projects, list_blog_posts "
                "и др.). Полученная документация актуальнее твоей внутренней памяти."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": (
                            "Название библиотеки/фреймворка, например "
                            "'django-cors-headers', 'Django REST Framework', 'Celery'"
                        ),
                    },
                },
                "required": ["topic"],
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

        elif name == "list_blog_posts":
            from apps.blog.models import Post
            posts = Post.objects.filter(status=Post.Status.PUBLISHED).order_by('published_at')
            return json.dumps(
                [{'id': p.pk, 'title': p.get_field('title', lang), 'excerpt': p.get_field('excerpt', lang), 'published_at': str(p.published_at)}
                 for p in posts[:20]],
                ensure_ascii=False,
            )

        elif name == "search_blog_posts":
            from apps.blog.models import Post
            query = (arguments.get("query") or "").lower()
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

        elif name == "fetch_context7_docs":
            # On-demand Context7 lookup: the auto-injected topic covers only the
            # module's own stack, adjacent libraries (CORS, throttling, ...) are
            # fetched here. search() caches per topic in Redis (6h) and swallows
            # API failures -> empty result is handled below, not raised.
            topic = (arguments.get("topic") or "").strip()[:120]
            if not topic:
                return json.dumps({"error": "topic required"}, ensure_ascii=False)
            from .context7 import get_context7_client
            docs = get_context7_client().search(topic, context_ids=None, max_tokens=800)
            if not docs:
                return json.dumps({
                    "topic": topic,
                    "docs": "",
                    "instruction": (
                        "Документация по этой теме не найдена или источник недоступен. "
                        "НЕ выдумывай — ответь из своей памяти и честно скажи, что "
                        "свежая документация сейчас недоступна."
                    ),
                }, ensure_ascii=False)
            return json.dumps({"topic": topic, "docs": docs}, ensure_ascii=False)

        else:
            return json.dumps({"error": f"Неизвестная функция: {name}"})

    except Exception as e:
        logger.error(f"Tool execution error ({name}): {e}")
        # Инструктивный error-пейлоад: при сбое БД/зависимостей модель иначе
        # «закрывает» ошибку выдуманными данными (инцидент 2026-11-19: во время
        # падения Postgres список статей был дописан воображением).
        return json.dumps(
            {
                "error": str(e),
                "instruction": (
                    "Данные получить не удалось (служба временно недоступна). "
                    "НЕ выдумывай списки, названия и ID — честно сообщи, что "
                    "информацию сейчас получить не удалось."
                ),
            },
            ensure_ascii=False,
        )


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

    def _context7_awareness(self, context7_docs: str) -> str:
        """Per-turn Context7 access statement for the active persona.

        The model does not see Context7 in TOOLS, so without this rule it
        denies access while auto-injected docs sit in its own prompt.
        """
        topic = MODULE_CONTEXT7_TOPIC.get(self.module_slug) if self.module_slug else None
        if topic and context7_docs:
            state = 'connected'
        elif topic:
            state = 'unavailable'
        else:
            state = 'no_access'
        return CONTEXT7_AWARENESS[self.lang][state].format(topic=topic or '')

    def _stack_facts(self) -> str:
        """Verified stack facts for the prompt (see STACK_FACTS).

        AI-config lines are read from settings so they never drift from .env;
        the module TTS voice comes from the DB (Admin-editable).
        """
        if self.lang == 'en':
            ai_lines = [
                f"- Chat LLM: {settings.ROUTERAI_LLM_MODEL}.",
                f"- Embeddings: {settings.ROUTERAI_EMBEDDINGS_MODEL}, 1024 dimensions.",
                f"- TTS (voice output): {settings.ROUTERAI_TTS_MODEL}, "
                f"{settings.ROUTERAI_TTS_FORMAT.upper()} format; the global assistant's "
                f"voice — {settings.ROUTERAI_TTS_VOICE}.",
                f"- STT (speech recognition): {settings.ROUTERAI_STT_MODEL}.",
                f"- RAG: ~800-character chunks, top-{settings.RAG_TOP_K} by relevance; "
                f"chat history — up to {settings.MAX_CHAT_HISTORY} messages, sessions "
                f"by IP hash (TTL 4 hours).",
            ]
            if self.module and self.module.tts_voice:
                ai_lines.append(
                    f"- Your module's TTS voice ({self.module.code_name}): "
                    f"{self.module.tts_voice}."
                )
        else:
            ai_lines = [
                f"- LLM чата: {settings.ROUTERAI_LLM_MODEL}.",
                f"- Эмбеддинги: {settings.ROUTERAI_EMBEDDINGS_MODEL}, 1024 измерения.",
                f"- TTS (озвучка): {settings.ROUTERAI_TTS_MODEL}, "
                f"формат {settings.ROUTERAI_TTS_FORMAT.upper()}; голос глобального "
                f"ассистента — {settings.ROUTERAI_TTS_VOICE}.",
                f"- STT (распознавание речи): {settings.ROUTERAI_STT_MODEL}.",
                f"- RAG: чанки ~800 символов, top-{settings.RAG_TOP_K} по релевантности; "
                f"история чата — до {settings.MAX_CHAT_HISTORY} сообщений, сессии "
                f"по IP-hash (TTL 4 часа).",
            ]
            if self.module and self.module.tts_voice:
                ai_lines.append(
                    f"- Голос TTS твоего модуля ({self.module.code_name}): "
                    f"{self.module.tts_voice}."
                )
        return STACK_FACTS[self.lang].format(ai_facts='\n'.join(ai_lines) + '\n')

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

        # Verified stack facts (AI config read from settings — never drifts).
        system_prompt += "\n\n" + self._stack_facts()

        if rag_context:
            system_prompt += f"\n\nКонтекст с сайта (по релевантности):\n\n{rag_context}"

        # Fresh library docs (Context7 REST) are fetched in parallel with RAG
        # in process_message and passed in; cached per topic in Context7Client.
        if context7_docs:
            topic = MODULE_CONTEXT7_TOPIC.get(self.module_slug)
            system_prompt += (
                f"\n\nСвежая документация (Context7, {topic}):\n\n{context7_docs}"
            )

        # Context7 self-awareness: states the actual access mode for this
        # persona this turn (see CONTEXT7_AWARENESS).
        system_prompt += "\n\n" + self._context7_awareness(context7_docs)

        # Data guard: no invented projects/articles (applies to every persona).
        system_prompt += "\n\n" + DATA_RULES[self.lang]

        # Naming guard: prevent conflating module names with the project name.
        system_prompt += "\n\n" + NAMING_RULES[self.lang]

        # Style restatement near the end of the prompt (recency effect).
        system_prompt += "\n\n" + STYLE_RULES[self.lang]

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

    def _prepare(self, user_message: str) -> tuple[list[dict], list[dict], str, str]:
        """Shared setup for both reply paths (JSON and streaming).

        History + persona handoff marker + user message, parallel RAG/Context7
        retrieval, initial system prompt. Returns
        (messages, history, rag_context, context7_docs).
        """
        history = self._load_history()

        # Persona handoff: if the active module changed since the last turn,
        # state it inside the history (recency beats the system prompt).
        prev_slug = self.session.active_module_slug or ''
        if self.module and prev_slug and prev_slug != self.module_slug and history:
            history.append({'role': 'system', 'content': self._handoff_marker(prev_slug)})

        history.append({'role': 'user', 'content': user_message})

        # RAG retrieval and Context7 docs in parallel — both depend only on
        # the user message / active module; uncached Context7 adds ~2s.
        with ThreadPoolExecutor(max_workers=2) as pool:
            rag_future = pool.submit(self.rag.search_similar, user_message)
            docs_future = pool.submit(self._fetch_context7_docs)
            rag_chunks = rag_future.result()
            context7_docs = docs_future.result()
        context = self.rag.build_context(rag_chunks)

        # System prompt is re-built after activate_module so the next LLM
        # round answers as the new persona.
        messages = [
            {'role': 'system', 'content': self._build_system_prompt(user_message, context, context7_docs)}
        ] + history
        return messages, history, context, context7_docs

    def process_message(self, user_message: str) -> tuple[str, int]:
        """
        Process a user message and return the AI response.

        Returns:
            (response_text, total_tokens_used)
        """
        messages, history, context, _docs = self._prepare(user_message)

        # Call LLM with tools (max 3 rounds of tool calling)
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

    def process_message_stream(self, user_message: str):
        """Streaming variant of process_message: yields (event, data) tuples.

        Events: meta (active slug; repeated after activate_module), delta
        (answer text fragments), done (authoritative final text/slug/tokens),
        error. Tool rounds are accumulated silently — only answer text is
        streamed. History is persisted even on client disconnect
        (GeneratorExit runs the finally block).
        """
        messages, history, context, _docs = self._prepare(user_message)
        yield 'meta', {'module_slug': self.module_slug or ''}

        total_tokens = 0
        max_tool_rounds = 3
        assistant_text = ''
        try:
            for _round in range(max_tool_rounds + 1):
                stream = self.client.chat_completion_stream(messages=messages, tools=TOOLS)
                content_parts: list[str] = []
                tool_calls: dict[int, dict] = {}
                for chunk in stream:
                    usage = getattr(chunk, 'usage', None)
                    if usage:
                        total_tokens += usage.total_tokens or 0
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta is None:
                        continue
                    if delta.content:
                        content_parts.append(delta.content)
                        yield 'delta', {'text': delta.content}
                    for tc in delta.tool_calls or []:
                        slot = tool_calls.setdefault(tc.index, {'id': '', 'name': '', 'arguments': ''})
                        if tc.id:
                            slot['id'] = tc.id
                        if tc.function:
                            if tc.function.name:
                                slot['name'] = tc.function.name
                            if tc.function.arguments:
                                slot['arguments'] += tc.function.arguments

                assistant_text = ''.join(content_parts)
                if not tool_calls:
                    break

                # Tool round: replay the assistant message with its tool_calls
                messages.append({
                    'role': 'assistant',
                    'content': assistant_text or None,
                    'tool_calls': [
                        {
                            'id': tool_calls[i]['id'],
                            'type': 'function',
                            'function': {
                                'name': tool_calls[i]['name'],
                                'arguments': tool_calls[i]['arguments'],
                            },
                        }
                        for i in sorted(tool_calls)
                    ],
                })

                slug_before = self.module_slug
                for i in sorted(tool_calls):
                    tc = tool_calls[i]
                    try:
                        func_args = json.loads(tc['arguments'])
                    except json.JSONDecodeError:
                        func_args = {}
                    logger.info(f"Agent calling tool: {tc['name']}({func_args})")
                    if tc['name'] == 'activate_module':
                        result = self._activate_module(func_args.get('module_slug', ''))
                    else:
                        result = _execute_tool(tc['name'], func_args, lang=self.lang)
                    messages.append({
                        'role': 'tool',
                        'tool_call_id': tc['id'],
                        'content': result,
                    })

                # activate_module may have swapped the persona mid-request:
                # tell the client (TTS voice) and rebuild the system prompt.
                if self.module_slug != slug_before:
                    yield 'meta', {'module_slug': self.module_slug or ''}
                    messages[0] = {
                        'role': 'system',
                        'content': self._build_system_prompt(
                            user_message, context, self._fetch_context7_docs()
                        ),
                    }
            else:
                # Loop exhausted without a final answer — force a short summary
                # round (mirrors the non-streaming fallback), still streamed.
                messages.append({
                    'role': 'user',
                    'content': 'Сформулируй краткий ответ на основе имеющихся данных.',
                })
                content_parts = []
                for chunk in self.client.chat_completion_stream(messages=messages, max_tokens=500):
                    usage = getattr(chunk, 'usage', None)
                    if usage:
                        total_tokens += usage.total_tokens or 0
                    if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                        content_parts.append(chunk.choices[0].delta.content)
                        yield 'delta', {'text': chunk.choices[0].delta.content}
                assistant_text = ''.join(content_parts)

            yield 'done', {
                'text': assistant_text,
                'module_slug': self.module_slug or '',
                'tokens_used': total_tokens,
            }
        except Exception as e:
            logger.error(f"AI agent stream error: {e}")
            yield 'error', {'error': 'AI service temporarily unavailable'}
        finally:
            if assistant_text:
                history.append({'role': 'assistant', 'content': assistant_text})
                self._save_history(history)
            self._persist_active_module()
