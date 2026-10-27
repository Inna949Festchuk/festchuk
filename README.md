# 🌃 Festchuk — AI-Driven Cyberpunk Portfolio

Персональный сайт-портфолио уровня Middle+/Senior Fullstack-разработчика с интегрированным AI-ассистентом. Строго тёмная киберпанк-тема.

## ✨ Возможности

- **Портфолио** — проекты в Bento Grid, рендеринг README из GitHub, лайки и просмотры
- **Технический блог** — Markdown (таблицы, код, изображения), озвучка статей (TTS)
- **AI-ассистент** — RAG (pgvector), Function Calling, голосовой ввод (STT) и озвучка ответов (TTS)
- **Киберпанк UI** — неоновые акценты, glassmorphism, анимации Framer Motion
- **i18n** — RU / EN

## 🛠 Стек

| Слой | Технологии |
|------|-----------|
| Frontend | Next.js 14 (App Router), TypeScript, Tailwind CSS, Framer Motion, react-markdown |
| Backend | Python 3.12, Django 5, DRF, Celery + Beat |
| БД | PostgreSQL 15 + pgvector |
| Кэш / брокер | Redis 7 |
| AI | RouterAI (routerai.ru) — qwen-2.5-plus, bge-m3, whisper, tts-1-hd |
| Инфра | Docker Compose, Nginx |

## 📁 Структура (monorepo)

```
festchuk/
├── backend/                # Django
│   ├── apps/
│   │   ├── core/           # health check, базовые utils
│   │   ├── projects/       # модель Project, API, лайки/просмотры
│   │   ├── blog/           # модель Post, Markdown, TTS
│   │   ├── analytics/      # анонимные лайки/просмотры (Redis)
│   │   └── ai_agent/       # RAG, Function Calling, STT/TTS, Celery tasks
│   ├── config/             # settings, urls, celery, wsgi/asgi
│   ├── Dockerfile
│   ├── manage.py
│   └── requirements.txt
├── frontend/               # Next.js
│   ├── app/                # страницы (главная, проекты, блог, контакты)
│   ├── components/         # Header, ChatWidget
│   ├── Dockerfile
│   ├── next.config.js
│   ├── tailwind.config.js
│   └── package.json
├── nginx/
│   └── nginx.conf          # reverse proxy, rate limiting, WebSocket
├── docker-compose.yml      # production
├── docker-compose.dev.yml  # development (volume mounts)
├── .env.example
└── .gitignore / .dockerignore
```

## 🚀 Быстрый старт (разработка)

1. Скопировать и заполнить переменные окружения:
   ```bash
   cp .env.example .env
   # Внести: POSTGRES_PASSWORD, ROUTERAI_API_KEY и т.д.
   ```

2. Запустить все сервисы:
   ```bash
   docker compose -f docker-compose.dev.yml up -d --build
   ```

3. Применить миграции (при первом запуске):
   ```bash
   docker compose -f docker-compose.dev.yml exec backend python manage.py migrate
   ```

4. Создать суперпользователя для админки:
   ```bash
   docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser
   ```

5. Открыть:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000/api/
   - Админка: http://localhost:8000/admin/

## 📡 Основные API-эндпоинты

```
GET  /api/projects/              # список проектов
GET  /api/projects/{slug}/       # детали проекта
POST /api/projects/{id}/like/    # лайк (анонимный)
POST /api/projects/{id}/view/    # просмотр

GET  /api/posts/                 # список статей
GET  /api/posts/{slug}/          # детали статьи
POST /api/posts/{id}/like/       # лайк
POST /api/posts/{id}/tts/        # озвучка (TTS)

POST /api/chat/session/          # создать сессию чата
POST /api/chat/message/          # отправить сообщение
GET  /api/chat/history/{id}/     # история диалога
POST /api/chat/voice/stt/        # Speech-to-Text

GET  /api/stats/                 # агрегированная статистика
GET  /api/health/                # health check
```

## 🤖 AI-агент

AI-ассистент использует:
- **RAG** — векторные эмбеддинги README проектов и статей (pgvector), top-5 retrieval
- **Function Calling** — `get_project_stats`, `list_projects`, `search_blog_posts`, `get_blog_post`
- **Память** — история диалога в Redis (TTL 4 часа)
- **Голос** — Web Audio API → STT (Whisper) → LLM → TTS (tts-1-hd)

Celery задачи:
- `sync_project_readme` — скачивание README из GitHub + регенерация эмбеддингов
- `generate_post_embeddings` — эмбеддинги для статьи
- `sync_all_projects_readme` — периодический синк (ежедневно)

## 🔒 Безопасность

- Анонимные лайки/просмотры: hash IP + object_id в Redis, TTL 24ч
- Rate limiting: Nginx (30 r/s API, 5 r/s AI-эндпоинты) + DRF (100/hour anon)
- Без форм сбора ПДн (ФЗ-152)
- Cookie-баннер для Яндекс.Метрики (запланировано)

## 📝 Примечания

- **Ручное добавление проектов** — через Django Admin + возможность API
- **Markdown** — полный парсинг: GFM таблицы, подсветка кода, изображения
- **Киберпанк тема** — только тёмная, без переключения
