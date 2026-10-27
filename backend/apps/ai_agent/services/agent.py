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
from typing import Any

from django.conf import settings
from django.core.cache import cache

from .router_ai import RouterAIClient
from .rag import RAGService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
Ты — AI-ассистент на персональном сайте-портфолио разработчика Константина Фестчука.
Твоя задача — помогать посетителям узнать о проектах и статьях на сайте.

Правила:
- Отвечай на языке пользователя (русский или английский).
- Если вопрос о проектах или статьях — используй предоставленный контекст.
- Если контекст пуст или недостаточно информации — честно скажи, что не нашёл ответа, и предложи посмотреть сайт.
- Не выдумывай проекты или статьи, которых нет в контексте.
- Отвечай кратко и по делу, без лишних формальностей.
- Если вопрос не относится к сайту — вежливо направь на темы портфолио.
"""

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
]


def _execute_tool(name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool function and return the result as a string."""
    try:
        if name == "get_project_stats":
            from apps.projects.models import Project
            project = Project.objects.filter(pk=arguments["project_id"]).first()
            if not project:
                return json.dumps({"error": f"Проект {arguments['project_id']} не найден"})
            return json.dumps({
                "id": project.pk,
                "title": project.title,
                "description": project.summary,
                "technologies": project.technologies,
                "github_url": project.github_url,
                "views": project.views_count,
                "likes": project.likes_count,
            }, ensure_ascii=False)

        elif name == "list_projects":
            from apps.projects.models import Project
            projects = Project.objects.filter(visibility=Project.Visibility.PUBLIC).values(
                'pk', 'title', 'summary', 'technologies', 'github_url'
            )
            return json.dumps(list(projects), ensure_ascii=False)

        elif name == "search_blog_posts":
            from apps.blog.models import Post
            query = arguments["query"].lower()
            posts = Post.objects.filter(status=Post.Status.PUBLISHED)
            filtered = [
                p for p in posts
                if query in p.title.lower()
                or query in p.excerpt.lower()
                or any(query in tag.lower() for tag in p.tags)
            ]
            return json.dumps(
                [{'id': p.pk, 'title': p.title, 'excerpt': p.excerpt, 'published_at': str(p.published_at)}
                 for p in filtered[:10]],
                ensure_ascii=False,
            )

        elif name == "get_blog_post":
            from apps.blog.models import Post
            post = Post.objects.filter(pk=arguments["post_id"], status=Post.Status.PUBLISHED).first()
            if not post:
                return json.dumps({"error": f"Статья {arguments['post_id']} не найдена"})
            # Truncate content to avoid token overflow
            content = post.content[:3000]
            if len(post.content) > 3000:
                content += "\n\n[...контент урезан...]"
            return json.dumps({
                "id": post.pk,
                "title": post.title,
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

    def __init__(self, session):
        self.session = session
        self.client = RouterAIClient()
        self.rag = RAGService()

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

    def process_message(self, user_message: str) -> tuple[str, int]:
        """
        Process a user message and return the AI response.

        Returns:
            (response_text, total_tokens_used)
        """
        # 1. Load history
        history = self._load_history()

        # 2. Add current user message
        history.append({'role': 'user', 'content': user_message})

        # 3. RAG retrieval
        rag_chunks = self.rag.search_similar(user_message)
        context = self.rag.build_context(rag_chunks)

        # 4. Build system prompt with context
        system_prompt = SYSTEM_PROMPT
        if context:
            system_prompt += f"\n\nКонтекст с сайта (по релевантности):\n\n{context}"

        # 5. Build messages
        messages = [{'role': 'system', 'content': system_prompt}] + history

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
                return assistant_text, total_tokens

            # Process tool calls
            messages.append(choice.message.model_dump())

            for tool_call in choice.message.tool_calls:
                func_name = tool_call.function.name
                try:
                    func_args = json.loads(tool_call.function.arguments)
                except json.JSONDecodeError:
                    func_args = {}

                logger.info(f"Agent calling tool: {func_name}({func_args})")
                result = _execute_tool(func_name, func_args)

                messages.append({
                    'role': 'tool',
                    'tool_call_id': tool_call.id,
                    'content': result,
                })

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
        return final_text, total_tokens
