# Festchuk — AI-Driven Cyberpunk Portfolio

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


---
## Обновление контента (seed_portfolio)

Команда `seed_portfolio` идемпотентна — можно запускать сколько угодно раз.

```bash
docker compose -f docker-compose.dev.yml exec backend python manage.py seed_portfolio
```

### Что делает

1. **Проекты (GitHub)** — перечисляет все публичные не-форк репозитории `Inna949Festchuk` через GitHub API, скачивает README и превью. Новые репозитории подхватываются автоматически.
2. **Статьи (Хабр)** — парсит страницу автора `habr.com/ru/users/dilmah949/articles/`, скачивает контент (HTML → markdown с картинками) и обложки. Новые статьи подхватываются автоматически.
3. **RAG-эмбеддинги** — генерирует vector embeddings для AI-ассистента (pgvector).

### Как добавить контент

| Источник | Что делаете вы | Что делает seed |
|----------|---------------|-----------------|
| **GitHub** | Запушиваете репозиторий | Название, описание, язык, README, превью — всё сам |
| **Хабр** | Публикуете статью | Текст, картинки, обложка, slug, дата — всё сам |

Кастомизация (опционально): через Django Admin (`http://localhost:8000/admin/`) — названия, описания, featured, порядок, обложки, теги, переводы EN.

### Защита от перезаписи (sync_from_source)

У каждой статьи/проекта есть флаг `sync_from_source` (по умолчанию **включён**).

- **При редактировании через Admin** флаг автоматически **выключается** — seed_portfolio перестаёт перезаписывать эту запись. Ваши правки сохраняются.
- **При запуске seed** записи с выключенным флагом пропускаются (в выводе: `(skipped: manual)`).
- **Чтобы снова синхронизировать** — включите флаг в Admin (`Синхронизировать с Хабром/GitHub`).

### Флаги

| Флаг | Назначение |
|------|-----------|
| `--force-images` | Перекачать обложки/превью даже если уже сохранены |
| `--no-images` | Не скачивать изображения |
| `--no-readme` | Не скачивать README / контент с Хабра |
| `--no-embed` | Пропустить генерацию RAG-эмбеддингов |
| `--flush` | Удалить ВСЕ статьи и проекты перед заполнением |

### Где хранятся файлы

- Обложки статей: `backend/media/blog/covers/`
- Превью проектов: `backend/media/projects/previews/`
- Картинки в теле статей — hotlink с `hadrastorage.org` (не скачиваются)
- Картинки в README проектов — hotlink с `raw.githubusercontent.com` (fallback main→master)

### Проверка результата

- Консоль: `• Article: ... cover ✓(author)`, `• Project: ... README ✓ img ✓`, `✔ Portfolio ready: N articles, M projects`
- Браузер: `http://localhost:3000/` (Ctrl+F5 для сброса кэша)
- Прямые файлы: `http://localhost:8000/media/blog/covers/...`

### Подводки

- **Dev-код:** при изменениях в Python-файлах Django StatReloader подхватит автоматически. Если работает через Docker prod (без volume mounts) — нужен `up -d --build`.
- **GitHub API limit:** без токена 60 req/hour на IP. При исчерпании seed пишет WARNING и работает по статическому списку.
- **Хабр:** при недоступности (нет сети / 403) fallback на локальные `.md` из `data/articles/`.