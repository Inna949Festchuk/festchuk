# QWEN.md — festchuk (Feshchuk Portfolio)

Инструкционный контекст для работы с репозиторием. Документация проекта ведётся на русском языке.

## Обзор проекта

Персональный сайт-портфолио Константина Фестчука («Feshchuk») с интегрированным AI-ассистентом. Строго тёмная киберпанк-тема (без переключения на светлую). Monorepo: Next.js-фронтенд + Django-бэкенд + PostgreSQL/pgvector + Redis + Celery + Nginx, всё запускается через Docker Compose.

Основные возможности: портфолио проектов (Bento Grid, README из GitHub), блог (Markdown, статьи с Хабра), AI-чат с RAG и Function Calling, голосовой ввод (STT) и озвучка (TTS), i18n RU/EN, анонимные лайки/просмотры.

## Стек

| Слой | Технологии |
|------|-----------|
| Frontend | Next.js 14.2 (App Router, `output: 'standalone'`), TypeScript, Tailwind CSS, Framer Motion, react-markdown + remark-gfm + rehype-highlight, next-intl, axios |
| Backend | Python 3.12, Django 5.0, DRF, Celery + django-celery-beat, Channels/Daphne |
| БД | PostgreSQL 15 + pgvector (образ `pgvector/pgvector:pg15`), эмбеддинги 1024d |
| Кэш/брокер | Redis 7 (кэш DB0, брокер DB1, результаты DB2) |
| AI | RouterAI (`https://routerai.ru/api/v1`, OpenAI-совместимый): LLM qwen3.7-plus, эмбеддинги bge-m3, TTS google/gemini-*-tts, STT whisper-large-v3-turbo; Context7 REST v1 для актуальной документации библиотек |
| Инфра | Docker Compose (dev и prod), Nginx (prod: reverse proxy, rate limiting, static/media) |

## Структура

```
festchuk/
├── backend/
│   ├── apps/
│   │   ├── core/        # health check, management-команды seed_*
│   │   ├── projects/    # Project, API, лайки/просмотры, GitHub-синк
│   │   ├── blog/        # Post, Markdown, TTS статей, Хабр-синк
│   │   ├── analytics/   # анонимные лайки/просмотры (Redis, IP-hash, TTL 24ч)
│   │   └── ai_agent/    # RAG, чат, STT/TTS, модули агентов, Celery tasks
│   │       └── services/  # agent.py, routing.py, rag.py, router_ai.py, context7.py
│   ├── config/          # settings, urls, celery, middleware, throttling, wsgi/asgi
│   ├── logs/django.log  # файловый лог (рантайм-артефакт)
│   └── requirements.txt
├── frontend/
│   ├── app/[locale]/    # страницы: главная, projects, blog, contacts, modules/[slug]
│   ├── components/      # Header, Footer, ChatWidget, CyberMusicPlayer, Cityscape,
│   │                    # AgentVideoCard, HudBottomGuard, LanguageSwitcher, …
│   ├── i18n/            # routing/request/navigation (next-intl)
│   ├── messages/        # ru.json, en.json — ВСЕ пользовательские строки
│   ├── middleware.ts    # locale-редиректы
│   └── next.config.js   # rewrite /api/* → backend, trailingSlash, proxyTimeout
├── nginx/nginx.conf     # только prod
├── docker-compose.yml       # production (gunicorn, nginx, без volume mounts кода)
├── docker-compose.dev.yml   # development (volume mounts, runserver, next dev)
└── .env.example             # ТОЛЬКО плейсхолдеры, реальные ключи не коммитить
```

## Сборка и запуск

Вся разработка идёт через dev-compose. Контейнеры: `feshchuk-dev-{postgres,redis,backend,celery,celery-beat,frontend}`. Порты: frontend `3000`, backend `8000`, postgres `5432`, redis `6379`.

```bash
cp .env.example .env   # заполнить POSTGRES_PASSWORD, DJANGO_SECRET_KEY, ROUTERAI_API_KEY, CONTEXT7_API_KEY

# Запуск / пересборка
docker compose -f docker-compose.dev.yml up -d --build

# Миграции
docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations
docker compose -f docker-compose.dev.yml exec backend python manage.py migrate

# Суперпользователь
docker compose -f docker-compose.dev.yml exec backend python manage.py createsuperuser

# Наполнение контентом (идемпотентно)
docker compose -f docker-compose.dev.yml exec backend python manage.py seed_portfolio
docker compose -f docker-compose.dev.yml exec backend python manage.py seed_modules

# Логи
docker compose -f docker-compose.dev.yml logs -f backend celery frontend
```

Prod: `docker compose up -d --build` (backend сам делает `migrate` + `collectstatic`, gunicorn 4 workers; nginx отдаёт static/media и проксирует). После правок кода в prod — rebuild образа, в dev — достаточно restart (см. ниже).

### Dev-воркфлоу: restart vs rebuild

В dev настроены volume mounts (`./backend:/app`, `./frontend:/app`), код синхронизируется автоматически:

| Изменение | Действие |
|-----------|----------|
| Python-код backend | Django runserver перезагрузится сам (StatReloader); Celery — `docker compose -f docker-compose.dev.yml restart celery` |
| Frontend TS/TSX/CSS | Next dev подхватит автоматически (HMR); при сомнениях — `restart frontend` |
| Dockerfile, requirements.txt, package.json, системные пакеты | `up -d --build <service>` |
| Новая `command`/env в compose | `up -d --force-recreate <service>` |
| Новый env-файл `.env` | `up -d --force-recreate` затронутых сервисов |

Осторожно: StatReloader прерывает in-flight запросы при правке Python-файлов — не редактировать backend во время долгих запросов (чат, seed).

### Проверка изменений (тестов нет)

Автотестов в репозитории сейчас нет (pytest/pytest-django в requirements, но test-файлов не существует). Верификация:

```bash
# TypeScript — ТОЛЬКО внутри контейнера (на хосте EACCES/зависание из-за root-owned tsconfig.tsbuildinfo)
docker compose -f docker-compose.dev.yml exec -T frontend npx tsc --noEmit

# ESLint в репозитории не настроен (next lint спрашивает конфиг интерактивно) — основной чек tsc

# Django-проверки
docker compose -f docker-compose.dev.yml exec backend python manage.py check

# Смоук API
curl -s http://localhost:8000/api/health/
curl -s http://localhost:8000/api/projects/
```

Плюс ручная проверка в браузере (http://localhost:3000) и чтение логов (`backend/logs/django.log`, `docker compose logs`). EACCES на `tsconfig.tsbuildinfo` при хостовом tsc — не ошибка типов, а права; гнать tsc в контейнер.

## Архитектура и ключевые механизмы

### Прокси frontend → backend (ловушки)

- Браузер ходит в Next.js `/api/*`, Next rewrite проксирует на `API_PROXY_TARGET` (в Docker — `http://backend:8000`, НЕ localhost). Таймаут прокси `experimental.proxyTimeout: 180000` — чат с RAG отвечает дольше дефолтных 30s.
- `trailingSlash: true` в next.config + `config.middleware.ApiTrailingSlashMiddleware` в Django (дописывает слэш на месте, без 301) — иначе петля редиректов Next 308 ↔ Django APPEND_SLASH 301. Не ломать эту пару.
- `API_BASE_URL` (env) задаёт абсолютный base для media-URL в ответах API: backend видит только внутренние Host (`backend:8000`), браузер их не резолвит.

### API полностью анонимный

`DEFAULT_AUTHENTICATION_CLASSES = ()` намеренно: SessionAuthentication при залогиненной Django-админке включал бы CSRF на POST, и SPA без X-CSRFToken получала бы 403 на чате/STT. Не возвращать session-auth «для удобства». Троттлинг — `config.throttling.ClientIPAnonRateThrottle` по реальному IP (приватные/Docker-адреса доверены всегда, публичные прокси — через `TRUSTED_PROXY_IPS`). Ставки из env: anon 2000/h, write 120/h, chat/stt 30/h, tts 120/h (кусочный синтез — несколько запросов на ответ). В dev весь трафик идёт через rewrite Next без X-Forwarded-For — anon-бакет общий на весь сайт.

### AI-ассистент: модули и маршрутизация

PRIME COORDINATOR (slug `prime-coordinator`) — дирижёр по умолчанию; четыре модуля: HYPER DRIVE (бэкенд), QUANTUM SHIELD (безопасность), NEURAL SYNC (AI), OMNI VISION (фронтенд). Персоны, SKILL-промпты, голоса TTS, приветствия и ключевые слова роутинга хранятся в БД (`AgentModule`) и редактируются в Django Admin — не хардкодить в Python.

Два слоя роутинга:
1. Детерминированный (`services/routing.py`): имя модуля в тексте → ключевые слова стека (`routing_keywords`, фолбэк `DEFAULT_ROUTING_KEYWORDS`) → триггеры возврата («пока»/«bye»/«помощник» — отдельное слово, «покажи» не переключает) → закреплённый slug сессии.
2. Семантический: LLM отвечает в персоне активного модуля и может вызвать инструмент `activate_module` для передачи диалога.

`ChatSession.active_module_slug` — маркер персоны прошлого хода. Сессии по IP-hash (unique), TTL 4ч, история в `ChatMessage` (до 16 сообщений в контексте, `MAX_CHAT_HISTORY`). Состав каталога (наличие/отсутствие/полные списки/сопоставления) модель подтверждает ТОЛЬКО инструментами (`list_projects`, `list_blog_posts`, …); RAG-контекст — детали, не основание для выводов о составе. Правило `DATA_RULES` добавляется в коде к каждой персоне (глобальный SYSTEM_PROMPT с «не выдумывай» НЕ действует при наличии SKILL в БД; версия «или из контекста» давала пропуск инструментов и выдуманные списки).

### RAG и RouterAI

- `DocumentEmbedding` (pgvector, 1024d), чанки ~800 символов, top-3 (`RAG_TOP_K`). Вектор запроса кэшируется в Redis (`rag:qemb:{md5}`, TTL 1ч) — защита от всплесков латентности embeddings. Эмбеддинги генерируют Celery-задачи: `sync_project_readme`, `generate_post_embeddings`, `sync_all_projects_readme` (beat: ежедневно).
- RouterAI base URL — `https://routerai.ru/api/v1` (хост `api.routerai.ru` не резолвится с хоста).
- TTS: имена голосов специфичны для провайдера — `google/gemini-*-tts` принимают Gemini-имена (Puck/Zephyr/Charon/…), `minimax/speech-*` — OpenAI (alloy/nova/echo). Неверное имя → 400. Google TTS всегда отдаёт WAV. Голос модуля — `AgentModule.tts_voice`, глобальный — `ROUTERAI_TTS_VOICE`. Формат `wav` обязателен (дефолт SDK — raw PCM, браузер не играет).
- STT: multipart обязан содержать имя файла, иначе 400.
- Context7 — REST v1 (`CONTEXT7_BASE_URL=https://context7.com/api/v1`), используется модульными агентами для актуальной документации; доки кэшируются в Redis по topic (`CONTEXT7_CACHE_TTL`, 6ч).

### Стриминг ответа (SSE)

Чат стримится через `POST /api/chat/message/stream/` (обычный JSON-эндпоинт сохранён для совместимости). События: `meta` (slug активной персоны; повторяется после `activate_module`) → `delta` (фрагменты текста) → `done` (авторитетный итоговый текст, slug, токены, message_id); `error` при сбое. Генератор `AIAgent.process_message_stream` стримит только текст финального раунда — tool-раунды копятся молча; история и сообщение сохраняются даже при обрыве клиента (finally). `ChatWidget` парсит SSE вручную (fetch + ReadableStream, EventSource не умеет POST), батчит рендер ~60мс. TTS потоковый: `createTTSChunker` на лету вырезает законченные предложения (150–450 знаков; лимит эндпоинта — 500/запрос), очередь синтезирует и играет их с prefetch следующего во время воспроизведения — голос сопровождает текст, не дожидаясь `done`; markdown очищается, код-блоки не режутся посередине; модель и голоса не менять. Обязательные детали: заголовки `Cache-Control: no-cache, no-transform` (обход compression-мидлвари Next) + `X-Accel-Buffering: no`; nginx `/api/chat/` — `proxy_buffering off`; в DRF-вьюхе override `perform_content_negotiation` (иначе `Accept: text/event-stream` → 406). **`stream_options.include_usage` не ставить** — RouterAI с ним буферизует весь ответ (TTFT 15,8с против ~1с); usage приходит в финальном чанке по умолчанию.

### Контент: seed_portfolio

Идемпотентная команда: перечисляет публичные не-форк репозитории GitHub (`Inna949Festchuk`), парсит статьи автора Хабра (`dilmah949`), скачивает README/контент/обложки, генерирует RAG-эмбеддинги. Флаги: `--force-images`, `--no-images`, `--no-readme`, `--no-embed`, `--flush` (удалить ВСЁ перед заполнением — осторожно).

Защита кастомизации: записи, отредактированные в Admin, seed не затирает; флаг «Синхронизировать» в Admin управляет обновлением из источника. «Избранное» (featured) — ровно 6 проектов на главной в bento-сетке (1 large + 5 small). Обложки статей должны совпадать с превью на странице автора Хабра; whitelist скачивания картинок не включает habr.com — учитывать при правках.

### i18n

next-intl, URL-префиксы `/ru` `/en` (localePrefix always, default ru). Модели — поля `*_ru`/`*_en` с фоллбеком на RU через `get_field(field, lang)`; API принимает `?lang=ru|en`; чат получает `lang`. EN-поля в БД пусты — пользователь заполняет их через Admin, не ожидать EN-контента. Новые пользовательские строки добавлять ОБА файла: `messages/ru.json` и `messages/en.json`.

### UI-инварианты

- Только тёмная киберпанк-тема; display-шрифт Geologica (self-hosted через next/font).
- HUD-геометрия: body `flex min-h-screen flex-col`, контент `flex-1`, футер `shrink-0`. Плеер (слева) и чат (справа) фиксированы к нижним углам через CSS-переменную `--hud-bottom`, которую выставляет `HudBottomGuard.tsx` (подключён в `layout.tsx` после ChatWidget) — над въезжающим футером панели поднимаются. Не ломать эту цепочку.
- `.cyber-frame` ломает `position: fixed` у потомков — не помещать fixed-элементы внутрь рамки.
- Никаких появляющихся/выезжающих анимаций у модалок и панелей (подтверждённое требование пользователя).
- Страницы App Router с useState/useEffect/motion — `'use client'`.
- ChatWidget подключён глобально в `app/[locale]/layout.tsx`; после правок чата проверять, что dev-сборка подхватила изменения (старая JS-сборка давала расхождение голоса и текста).

## Конвенции разработки

- **Кастомизация контента — через Django Admin**, не через правки Python-файлов/сидов. Подсказки пользователю формулировать в терминах Admin.
- **Комментарии** в коде — на русском, объясняют «почему» (скрытые ограничения, ловушки), а не «что». Стиль существующих комментариев в settings.py/next.config.js — ориентир.
- **Конфигурация — через env** (`.env`, читается через python-dotenv и compose `env_file`). Гибкие унифицированные решения предпочтительнее хардкода. `.env.example` — только плейсхолдеры.
- **Безопасность оценивать проактивно** до реализации:(rate limiting, CSRF/CORS, отсутствие ПДн-форм — ФЗ-152, IP-hash вместо сырых IP).
- **Git**: ветка `master`, коммиты в стиле `v0.0.XX` (инкремент версии). Remote — HTTPS, push работает через credential.helper store. `backend/celerybeat-schedule` и `backend/logs/django.log` — рантайм-артефакты, постоянно «грязные» в git status; не включать их в функциональные коммиты без необходимости. Не пушить без явной просьбы.
- **Отладочный мусор убирать** после завершения задачи (временные логи, print/console.log, тестовые данные).
- README — только актуальное состояние, простые таблицы «действие → результат», без сравнений со старым и без технических деталей.
- Пользователь (Константин) может коммитить и править файлы параллельно в других терминалах — перечитывать файлы перед правками, не затирать чужие изменения.

## Известные ловушки (кратко)

1. tsc на хосте → EACCES/зависание; только `docker compose exec -T frontend npx tsc --noEmit`.
2. Next rewrite ↔ Django APPEND_SLASH → 301-петля; слэш-мидлварь + trailingSlash обязательны.
3. SessionAuthentication в DRF → 403 на POST при открытой админке; auth классы пусты намеренно.
4. `api.routerai.ru` не резолвится → «Connection error»; base URL `routerai.ru/api/v1`.
5. Голос TTS не от того провайдера → 400; Google TTS → всегда WAV; формат должен быть задан явно.
6. STT без имени файла в multipart → 400.
7. Дефолтный proxyTimeout Next (30s) режет чат → 500; стоит 180000.
8. Media-URL без `API_BASE_URL` указывают на `backend:8000` — браузер не открывает.
9. RAG молча не работает без миграции pgvector (`CREATE EXTENSION vector`, колонка embedding 1024d) и пересоздания контейнеров после правок `.env` (`env_file` читается только при create).
10. Правки SKILL-файлов `.md` не действуют, пока не синхронизированы в БД (источник истины — `AgentModule` в Admin).
11. `stream_options.include_usage` в стриме RouterAI → буферизация всего ответа (TTFT 15,8с); usage и так приходит в финальном чанке.
12. SSE в DRF: `Accept: text/event-stream` → 406 без override `perform_content_negotiation`; без `no-transform` в Cache-Control Next-прокси буферизует стрим.