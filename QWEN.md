# QWEN.md — festchuk (Feshchuk Portfolio)

Инструкционный контекст для работы с репозиторием. Документация и комментарии в коде ведутся на русском языке.
*(Объединённый стандарт для Qwen Code CLI, AGENTS.md и IDE-агентов в контекстном окне 120k).*

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
| AI | RouterAI (`https://routerai.ru/api/v1`, OpenAI-совместимый): LLM qwen3.7-plus (reasoning off), эмбеддинги bge-m3, TTS google/gemini-*-tts (голос Puck), STT whisper-large-v3-turbo; Context7 REST v1 для актуальной документации библиотек |
| Инфра | Docker Compose (dev и prod), Nginx (prod: reverse proxy, rate limiting, static/media) |

## Протокол работы агента (оптимизация под контекст 120k)

Чтобы не переполнять контекстное окно и сохранять высокую скорость работы (prefill):
1. **Точечное чтение файлов:** Не загружай крупные файлы целиком. Сначала ищи нужные символы/строки через поиск (`grep` / `rg`) и читай только релевантные диапазоны строк.
2. **Жёсткие исключения при сканировании:** Никогда не читай и не индексируй:
   - `backup_*.sql` (дампы БД)
   - `backend/logs/django.log` целиком (читай только последние `tail -n 50` строк при отладке)
   - `backend/media/`, `backend/static/`, `backend/celerybeat-schedule`, `nginx/ssl/`
   - `frontend/node_modules/`, `frontend/.next/`, `frontend/tsconfig.tsbuildinfo`, `frontend/package-lock.json`
3. **План перед правкой:** Если задача затрагивает >2 файлов или связку Backend + Frontend + БД, сначала сформулируй краткий план изменений, затем вноси правки пошагово.
4. **Синхронизация Fullstack-контрактов:** При изменении полей в Django-моделях (`models.py`) или DRF-сериализаторах (`serializers.py`) обязательно проверь и обнови соответствующие TypeScript-интерфейсы и вызовы API во `frontend/`.
5. **Автономная верификация:** После каждой кодовой правки прогоняй профильные проверки (`manage.py check`, `pytest`, `npx tsc --noEmit` в контейнере) и убирай временный отладочный мусор.

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
│   │       ├── services/  # agent.py, routing.py, rag.py, router_ai.py, context7.py,
│   │       │              # session.py (Redis-сессии), pii.py (PII-маскер), budget.py
│   │       ├── skills/    # SKILL_*.md — персоны-промпты модулей (seed_modules → БД)
│   │       ├── legal/     # fz_152_2026.txt — исходный текст 152-ФЗ; bootstrap LegalDocument (Admin), seed_legal_docs
│   │       ├── management/ # seed_legal_docs — эмбеддинги 152-ФЗ в pgvector
│   │       └── tests/     # unit-тесты PII-маскера (pytest, без БД)
│   ├── config/          # settings, urls, celery, middleware, throttling, wsgi/asgi
│   ├── logs/django.log  # файловый лог (рантайм-артефакт)
│   └── requirements.txt
├── frontend/
│   ├── app/[locale]/    # страницы: главная, projects, blog, contacts, privacy, modules/[slug]
│   ├── components/      # Header, Footer, ChatWidget, CyberMusicPlayer, Cityscape,
│   │                    # AgentVideoCard, HudBottomGuard, LanguageSwitcher, Hologram, Odometer
│   ├── lib/             # ttsText.ts — чистые функции постобработки TTS-текста
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
docker compose -f docker-compose.dev.yml exec backend python manage.py seed_legal_docs

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

### Проверка изменений

Первые автотесты в репозитории — PII-маскер (`backend/apps/ai_agent/tests/test_pii.py`, чистые функции, без БД и сети). Верификация:

```bash
# ПИИ-маскер и будущие тесты (pytest.ini в backend/ задаёт DJANGO_SETTINGS_MODULE)
docker compose -f docker-compose.dev.yml exec backend python -m pytest apps/ai_agent/tests/ -q

# TypeScript — ТОЛЬКО внутри контейнера (на хосте EACCES/зависание из-за root-owned tsconfig.tsbuildinfo)
docker compose -f docker-compose.dev.yml exec -T frontend npx tsc --noEmit

# ESLint в репозитории не настроен (next lint спрашивает конфиг интерактивно) — основной чек tsc

# Django-проверки и проверка несозданных миграций
docker compose -f docker-compose.dev.yml exec backend python manage.py check
docker compose -f docker-compose.dev.yml exec backend python manage.py makemigrations --check --dry-run

# Смоук API
curl -s http://localhost:8000/api/health/
curl -s http://localhost:8000/api/projects/
```

Плюс ручная проверка в браузере (http://localhost:3000) и чтение последних строк логов (`tail -n 50 backend/logs/django.log`, `docker compose -f docker-compose.dev.yml logs --tail=50`). EACCES на `tsconfig.tsbuildinfo` при хостовом tsc — не ошибка типов, а права; гнать tsc в контейнер.

## Архитектура и ключевые механизмы

### Прокси frontend → backend (ловушки)

- Браузер ходит в Next.js `/api/*`, Next rewrite проксирует на `API_PROXY_TARGET` (в Docker — `http://backend:8000`, НЕ localhost). Таймаут прокси `experimental.proxyTimeout: 180000` — чат с RAG отвечает дольше дефолтных 30s.
- `trailingSlash: true` в next.config + `config.middleware.ApiTrailingSlashMiddleware` в Django (дописывает слэш на месте, без 301) — иначе петля редиректов Next 308 ↔ Django APPEND_SLASH 301. Не ломать эту пару.
- `API_BASE_URL` (env) задаёт абсолютный base для media-URL в ответах API: backend видит только внутренние Host (`backend:8000`), браузер их не резолвит.

### API полностью анонимный

`DEFAULT_AUTHENTICATION_CLASSES = ()` намеренно: SessionAuthentication при залогиненной Django-админке включал бы CSRF на POST, и SPA без X-CSRFToken получала бы 403 на чате/STT. Не возвращать session-auth «для удобства». Троттлинг — `config.throttling.ClientIPAnonRateThrottle` по реальному IP (приватные/Docker-адреса доверены всегда, публичные прокси — через `TRUSTED_PROXY_IPS`). Ставки из env: anon 2000/h, write 120/h, chat/stt 30/h, tts 120/h (кусочный синтез — несколько запросов на ответ). В dev весь трафик идёт через rewrite Next без X-Forwarded-For — anon-бакет общий на весь сайт. Лайки/просмотры: дедупликация в `AnalyticsService` (Redis-ключ по солённому хэшу IP + объект, TTL 24ч); вьюхи `like`/`view` после апдейта F() делают `refresh_from_db()` (иначе устаревший счётчик в ответе); API отдаёт `has_liked` в сериализаторах — фронтенд закрашивает сердечко и +1 к счётчику только на 200, не на 429. Просмотры страниц учитываются фронтендом вызовом `/view/` на детальных страницах.

### AI-ассистент: модули и маршрутизация

PRIME COORDINATOR (slug `prime-coordinator`) — дирижёр по умолчанию; четыре модуля: HYPER DRIVE (бэкенд), QUANTUM SHIELD (безопасность), NEURAL SYNC (AI), OMNI VISION (фронтенд). Персоны, SKILL-промпты, голоса TTS, приветствия и ключевые слова роутинга хранятся в БД (`AgentModule`) и редактируются в Django Admin — не хардкодить в Python. Исходные SKILL-файлы — `backend/apps/ai_agent/skills/SKILL_*.md`, они попадают в `system_prompt_ru/en` при `seed_modules`. **`seed_modules` — `update_or_create`: каждый прогон затирает ВСЕ поля модулей, включая Admin-правки (проверено 2026-11-21).** Точечная синхронизация (только нужные поля одной записи) — через `manage.py shell` (паттерн от 2026-11-21), не полным re-seed.

Два слоя роутинга:
1. Детерминированный (`services/routing.py`): имя модуля в тексте → ключевые слова стека (`routing_keywords`, фолбэк `DEFAULT_ROUTING_KEYWORDS`) → триггеры возврата («пока»/«bye»/«помощник» — отдельное слово, «покажи» не переключает) → закреплённый slug сессии.
2. Семантический: LLM отвечает в персоне активного модуля и может вызвать инструмент `activate_module` для передачи диалога. Инструменты у персон разные (2026-11-21): у PRIME COORDINATOR — только `activate_module` (`COORDINATOR_TOOLS` в agent.py), у специалистов — полный набор `TOOLS`. Координатор отвечает о составе портфолио (проекты/статьи/направления) по блоку «Карта портфолио» в промпте — `_portfolio_map()` собирает её из БД каждый ход (без кэша: два мелких SELECT'а, после правок Admin не отстаёт; ★ = featured), предметные детали передаёт специалисту.

Смена персоны обязательна к анонсу (решение 2026-11-20): `_handoff_marker` (system-сообщение ВНУТРИ истории перед сообщением пользователя при смене slug с прошлого хода) требует первым предложением объявить передачу или возврат к дирижёру; на ходах с tool-раундами напоминание дописывается к каждому tool-результату (`_handoff_reminder` — recency-бустер, без него анонс проигрывал tool-раундам и молча пропускался). Та же инструкция в result `activate_module`. Анонс — эталонная фраза строго от 1-го лица («Этот вопрос лежит в плоскости моей компетенции, и PRIME COORDINATOR передал мне диалог — я …»): модель копирует падеж и лицо из текста инструкции дословно, поэтому формулировка во 2-м лице («передал тебе») возвращалась в чат как реплика агента (исправлено 2026-11-27 во всех трёх точках, RU+EN). Анонс звучит ровно один раз: на ходе, где агент НЕ менялся, в историю добавляется `_anti_echo_marker` (детектирует фразу передачи в первой строке предыдущего ответа) — оговорка только в STYLE_RULES/маркере анонса повтор не останавливала, модель имитировала первую строку своего прошлого ответа.

Сессии и история — **только Redis** (решение 2026-11-21, 152-ФЗ; модели `ChatSession`/`ChatMessage` удалены миграцией 0009): `chat_session:{ip_hash}` (запись: session_id, `active_module_slug` — маркер персоны прошлого хода, created) и `chat_history:{session_id}` (до 16 сообщений, `MAX_CHAT_HISTORY`). TTL — слайдующий, `CHAT_RETENTION_HOURS` (дефолт 4 ч, `CHAT_SESSION_TTL = N*3600`): продлевается каждым действием (`session.touch()` / `_save_history`), удаление гарантирует движок Redis, а не периодическая задача. Гонка создания сессии — `cache.add()` (атомарный SETNX, замена unique-констрейнту БД; React 18 StrictMode дублирует mount в dev). Идентификация по запросам: `verify_session(ip_hash, session_id)` — чужой/протухший ID → 404. В Django Admin диалоги не видны (намеренно); вместо этого — анонимные счётчики `stats:pii_masked:{TYPE}` в Redis. PII-маскирование — в вьюхах ДО сохранения и ДО LLM/эмбеддингов (см. «Хранение чата и PII»). Состав каталога (наличие/отсутствие/полные списки/сопоставления) модель подтверждает ТОЛЬКО инструментами (`list_projects`, `list_blog_posts`, …); RAG-контекст — детали, не основание для выводов о составе. Правило `DATA_RULES` добавляется в коде к специалистам (к координатору вместо него — `COORDINATOR_RULES` + блок «Карта портфолио»; глобальный SYSTEM_PROMPT с «не выдумывай» НЕ действует при наличии SKILL в БД; версия «или из контекста» давала пропуск инструментов и выдуманные списки).

Кодовые правила промпта (agent.py, применяются ко ВСЕМ персонам, не редактируются в Admin): `CONTEXT7_AWARENESS` — честное самосознание доступа к Context7 по фактической подгрузке + приоритет источников (общие технические вопросы — доки Context7 + память; RAG — только «как устроено в этом портфолио»); `STACK_FACTS` — проверенные факты стека проекта (AI-строки берутся из settings, чтобы не дрейфовали от `.env`; срок хранения чата — `CHAT_RETENTION_HOURS`, не хардкодить); `PRIVACY_RULES` (2026-11-21) — не запрашивать ПДн, не восстанавливать плейсхолдеры ([PHONE], [EMAIL], …), факты о хранении — только из блока стека; языковые правила — язык ответа закреплён за UI-локалью, английский только как имена/термины внутри русских предложений.

### RAG и RouterAI

- `DocumentEmbedding` (pgvector, 1024d), чанки ~800 символов, top-3 (`RAG_TOP_K`). Вектор запроса кэшируется в Redis (`rag:qemb:{md5}`, TTL 1ч) — защита от всплесков латентности embeddings. Эмбеддинги генерируют Celery-задачи: `sync_project_readme`, `generate_post_embeddings`, `sync_all_projects_readme` (beat: ежедневно).
- RouterAI base URL — `https://routerai.ru/api/v1` (хост `api.routerai.ru` не резолвится с хоста).
- Источники RAG: `project` (README), `blog_post` (статьи) и `legal` — текст 152-ФЗ (ред. от 26.07.2026, 221 чанок) в модели `LegalDocument` (Admin → Нормативные документы; bootstrap строки из `apps/ai_agent/legal/fz_152_2026.txt` через `seed_legal_docs` — повторный запуск НЕ затирает Admin-правки). RAG-индекс обновляется ЯВНО экшеном «Проиндексировать в RAG» → Celery `embed_legal_document` (неактивный документ — чанки удаляются), не по сохранению (платные эмбеддинги). Поиск глобальный (без фильтра по типу) — юридические запросы сами поднимают legal-чанки в top-3. SKILL QUANTUM SHIELD обязывает отвечать по ПДн/152-ФЗ из этого контекста, цитировать только статьи, реально присутствующие в контексте, и оговаривать дату редакции; при смене текста/редакции в Admin дату в SKILL менять тоже (точечная синхронизация).
- LLM: qwen3.7-plus с `reasoning off` (`ROUTERAI_LLM_REASONING_ENABLED=false`) — в 3–9 раз быстрее и в 3–7 раз дешевле, качество на задачах портфолио не страдает; потолок `ROUTERAI_LLM_MAX_TOKENS=1000`.
- Суточный бюджет LLM (circuit breaker): `services/budget.py` — глобальные счётчики в Redis `stats:routerai:daily:{UTC-дата}:requests` / `:tokens` (TTL 48ч), лимиты из env `ROUTERAI_DAILY_MAX_REQUESTS` (1000) / `ROUTERAI_DAILY_MAX_TOKENS` (5M) — троттлинг per-IP не защищает от распределённого флуда. Пре-флайт-проверка в обеих chat-вьюхах → 429 с локализованным текстом; `claim_request()` и `record_tokens()` — в `AIAgent.process_message/process_message_stream`. Счётчики читаются `redis-cli`.
- TTS: имена голосов специфичны для провайдера — `google/gemini-*-tts` принимают Gemini-имена (Puck/Zephyr/Charon/…), `minimax/speech-*` — OpenAI (alloy/nova/echo). Неверное имя → 400. Google TTS всегда отдаёт WAV. Голос модуля — `AgentModule.tts_voice`, глобальный — `ROUTERAI_TTS_VOICE`. Формат `wav` обязателен (дефолт SDK — raw PCM, браузер не играет).
- STT: multipart обязан содержать имя файла, иначе 400.
- Context7 — REST v1 (`CONTEXT7_BASE_URL=https://context7.com/api/v1`), используется модульными агентами для актуальной документации; доки кэшируются в Redis по topic (`CONTEXT7_CACHE_TTL`, 6ч). Темы на модуль — `CONTEXT7_MODULE_TOPICS` (JSON slug→тема, пусто = дефолты из кода: hyper-drive=Django 5, neural-sync=LangChain, omni-vision=Next.js, quantum-shield=Django); после правки `.env` — `--force-recreate backend`. Смежные библиотеки, не покрытые темой модуля, агент запрашивает сам инструментом `fetch_context7_docs(topic)` (такой же лимит 800 токенов и кэш).

### Стриминг ответа (SSE)

Чат стримится через `POST /api/chat/message/stream/` (обычный JSON-эндпоинт сохранён для совместимости). События: `meta` (slug активной персоны; повторяется после `activate_module`) → `delta` (фрагменты текста) → `done` (авторитетный итоговый текст, slug, токены, message_id); `error` при сбое. Генератор `AIAgent.process_message_stream` стримит только текст финального раунда — tool-раунды копятся молча; история и сообщение сохраняются даже при обрыве клиента (finally). `ChatWidget` парсит SSE вручную (fetch + ReadableStream, EventSource не умеет POST), батчит рендер ~60мс. TTS потоковый: `createTTSChunker` на лету вырезает законченные предложения (150–450 знаков; лимит эндпоинта — 500/запрос), очередь синтезирует и играет их с prefetch следующего во время воспроизведения — голос сопровождает текст, не дожидаясь `done`; markdown очищается, код-блоки не режутся посередине; модель и голоса не менять. Обязательные детали: заголовки `Cache-Control: no-cache, no-transform` (обход compression-мидлвари Next) + `X-Accel-Buffering: no`; nginx `/api/chat/` — `proxy_buffering off`; в DRF-вьюхе override `perform_content_negotiation` (иначе `Accept: text/event-stream` → 406). **`stream_options.include_usage` не ставить** — RouterAI с ним буферизует весь ответ (TTFT 15,8с против ~1с); usage приходит в финальном чанке по умолчанию.

### Хранение чата и PII (152-ФЗ, решение 2026-11-21)

- **Хранение — только Redis.** Модели `ChatSession`/`ChatMessage` (PostgreSQL) удалены миграцией 0009. Диалоги: до 16 сообщений, слайдующий TTL `CHAT_RETENTION_HOURS` (дефолт 4 ч) — удаление гарантирует движок Redis, а не периодическая задача. В Django Admin диалоги не видны — намеренно.
- **PII-маскирование — на входе.** `services/pii.py` (чистые функции, unit-тесты `tests/test_pii.py`): email, карты (13–19 цифр + Luhn), паспорта РФ (серия + номер, по контексту «серия/номер» или 4+6 цифрам), СНИЛС и ИНН (с контрольными цифрами), телефоны РФ-мобильные (+7/8/7, третья цифра 9; 8-800 и случайные 11-значные не маскируются). Обе message-вьюхи применяют `mask_pii()` ДО сохранения и ДО LLM/эмбеддингов — ПДн не покидают периметр сервера. Плейсхолдеры: `[PHONE]`, `[EMAIL]`, `[PASSPORT]`, `[SNILS]`, `[INN]`, `[CARD]`. Путь STT закрыт: распознанный текст идёт в UI и в чат как обычное сообщение.
- **Право на удаление.** `DELETE /api/chat/session/` — идентификация строго по IP запроса (клиент не передаёт идентификаторов), chat-throttle (30/ч). Кнопка «Очистить диалог» в виджете реально удаляет данные на сервере и затем создаёт новую сессию.
- **Уведомления посетителю.** Строка под полем ввода («Диалог хранится до {N} ч, контакты и документы маскируются» + ссылка) — N приходит из API (`retention_hours`, из конфига; не хардкодить). Страница `/privacy` (RU/EN, namespace `privacy`) — честное описание обработки: маскирование перед внешней моделью, только RouterAI API-шлюз, без регистрации, IP-хэш.
- **Анонимные счётчики.** `stats:pii_masked:{TYPE}` в Redis (без ПДн) — замена удалённому admin-просмотру диалогов; читаются `redis-cli`.
- **Промпт.** `STACK_FACTS` сообщает персам реальные факты о хранении и маскировании (числа из settings). `PRIVACY_RULES` (code-level, все персоны) запрещают запрашивать ПДн и восстанавливать плейсхолдеры.

### Язык речи: TTS и STT

Речь должна держаться в языке интерфейса (RU по умолчанию). Две защиты:

- **Backend-пинга языка.** UI шлёт локаль: чат — поле `lang` в body, TTS/STT-эндпоинты — `?lang=ru|en`. TTS-вьюха (`ChatTTSView`) передаёт `lang` в `RouterAIClient.tts(language=...)`, где он уходит в `extra_body={'language': 'ru'}` (OpenAI SDK не типизирует `language` для audio.speech; RouterAI принимает, проверено 2026-11-20). Кэш TTS-ключа включает lang. STT шлёт `language` в whisper, иначе autodetect ошибается на коротких репликах.
- **Frontend-нормализация текста.** Синтезатор (Gemini) выбирает язык по плотности английского в куске: фразы, насыщенные терминами, он читает по-английски. `frontend/lib/ttsText.ts` (`normalizeTtsLanguage(text, en)`) — чистые функции без React/DOM (тестируются в node): убирает почти-английские скобки-глоссы (короткие теги ≤6 символов и русские глоссы остаются, включая осиротевшие скобки на границах чанка), заменяет английские связки русскими эквивалентами (`for example` → «например» и т.д.). Вызывается в `createTTSChunker` перед отправкой куска; `en=true` — pass-through (продукт русскоязычный). Перенос лейблов («Label — описание») из модуля удалён 2026-11-20: ломал грамматику в середине фразы и склеивал буллеты. Английские начала предложений режутся на уровне промпта (правила в agent.py).

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
- **Безопасность оценивать проактивно** до реализации: (rate limiting, CSRF/CORS, отсутствие ПДн-форм — ФЗ-152, IP-hash вместо сырых IP).
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
11. `stream_options.include_usage` в стриме RouterAI → буферизация всего ответа (TTFT 15,8с против ~1с); usage и так приходит в финальном чанке.
12. SSE в DRF: `Accept: text/event-stream` → 406 без override `perform_content_negotiation`; без `no-transform` в Cache-Control Next-прокси буферизует стрим.
13. Gemini TTS читает кусок по плотности английского → без `language=ru` (extra_body) и frontend-нормализации (`lib/ttsText.ts`) смешанные RU/EN ответы звучат по-английски.
14. TTS-чанкер не режет куски длиннее 450 знаков — бэкенд жёстко обрубает текст в 500 символов на запрос (`ChatTTSView`).
15. `seed_modules` затирает Admin-правки: `update_or_create` заменяет ВСЕ поля ВСЕХ модулей на каждый прогон (голоса, тексты, промпты). Точечные правки — через `manage.py shell` (паттерн 2026-11-21). Старое утверждение «не затирает» относилось к `seed_portfolio` (флаг `sync_from_source`), не к `seed_modules`.
16. Redis — критичное хранилище чата: вытеснение только `volatile-lru` (ключи с TTL). Не переключать на `allkeys-lru`: ключи брокера Celery (DB1) без TTL вытеснялись бы молча — потеря задач. `maxmemory` (`REDIS_MAXMEMORY`, дефолт 256mb) ограничивает RAM, а не диск: AOF живёт в томе `redis_data`, disk-full (инцидент 2026-11-19) всё так же рвёт записи.
17. «СИНТЕЗ ОТВЕТА...» висит долго (инцидент 2026-11-21) — RouterAI пилит латентностью (раунд, что обычно за 2–10 с, тянется на 60–120+ с), а OpenAI SDK без явного таймаута ждёт дефолтные 600 с. Лечится `ROUTERAI_TIMEOUT` (дефолт 180 с, `httpx.Timeout(180, connect=10)` в `RouterAIClient`) — зависший раунд падает с 503/ошибкой стрима, а не висит 10 минут. Сам runserver уже многопоточный по умолчанию (`--nothreading` его отключает; флага `--threaded` НЕТ — не добавлять).
