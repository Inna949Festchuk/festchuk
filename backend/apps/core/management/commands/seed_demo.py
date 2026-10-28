"""
Seed demo data: superuser + one portfolio project + one blog post.

Usage:
    python manage.py seed_demo
    python manage.py seed_demo --flush   # wipe demo project/post first (idempotent)

Credentials are read from env with dev fallbacks:
    SEED_ADMIN_USER, SEED_ADMIN_EMAIL, SEED_ADMIN_PASSWORD
"""
import os

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

from apps.projects.models import Project
from apps.blog.models import Post


DEMO_PROJECT_TITLE = 'Neural Grid — AI-платформа мониторинга'
DEMO_PROJECT_SLUG = 'neural-grid'
DEMO_POST_TITLE = 'Как я построил RAG-ассистента на pgvector + Qwen'
DEMO_POST_SLUG = 'rag-assistant-pgvector-qwen'

PROJECT_README = """\
## 🌐 Neural Grid

Решение реального времени для мониторинга сетевой инфраструктуры на базе
нейросетевой аномалии-детекции.

> **Статус:** production-ready · **Лицензия:** MIT

### Возможности

- Стриминг телеметрии в реальном времени (WebSocket + Celery)
- Детекция аномалий (autoencoder, окно 60 с)
- Dashboard с live-метриками и алертами
- Интеграция с Grafana / Prometheus / Slack

### Стек

| Слой | Технология |
|------|-----------|
| Frontend | Next.js 14, TypeScript, Framer Motion |
| Backend | Python 3.12, Django 5, DRF |
| Очередь | Celery + Redis |
| БД | PostgreSQL 15 + TimescaleDB |
| ML | PyTorch, ONNX Runtime |

### Установка

```bash
git clone https://github.com/Inna949Festchuk/neural-grid.git
cd neural-grid
docker compose up --build
```

### Метрики производительности

| Метрика | Значение |
|---------|---------|
| Latency (p99) | 42 ms |
| Throughput | 1.2M events/s |
| F1 (anomaly) | 0.94 |

### Roadmap

- [x] Базовый стриминг
- [x] Детекция аномалий
- [ ] Автоматическое масштабирование
- [ ] Мульти-арендность
"""

POST_CONTENT = """\
## Почему RAG, а не fine-tuning

Когда вам нужен ассистент, который отвечает по вашему контенту (проекты,
статьи, документация), **Retrieval-Augmented Generation** — почти всегда
правильный выбор. Не нужно дообучать модель — просто даёте ей релевантный
контекст в момент запроса.

### Архитектура

```
Пользователь → Prompt → [Retriever] → pgvector → [LLM: Qwen] → Ответ
                              ↑
                     эмбеддинги документов (bge-m3)
```

### Ключевые шаги

1. **Чанкинг** — режем README/статьи на блоки ~800 символов с перекрытием 100
2. **Эмбеддинг** — `bge-m3` (мультиязычная, 1024 dims)
3. **Хранилище** — `pgvector` прямо в PostgreSQL (отдельная векторная БД не нужна)
4. **Retrieval** — cosine similarity, top-5 чанков
5. **Генерация** — Qwen с контекстом + system-prompt

### Поисковый запрос

```sql
SELECT chunk_text,
       1 - (embedding <=> %s) AS similarity
FROM ai_agent_documentembedding
ORDER BY embedding <=> %s
LIMIT 5;
```

> `embedding <=> $1` — оператор косинусного расстояния pgvector. Чем меньше
> расстояние, тем ближе вектор.

### Итоги

| Аспект | Результат |
|--------|-----------|
| Латентность ответа | ~1.8 с |
| Точность retrieval | top-5 hit@5 = 0.88 |
| Стоимость | только LLM + эмбеддинги по запросу |

RAG даёт вам «живую» базу знаний, которую легко обновлять: синхронизировал
README — перегенерировал эмбеддинги — ассистент знает о новых проектах.
"""


class Command(BaseCommand):
    help = 'Seed demo data: superuser, one project, one blog post'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Delete existing demo project/post before creating (idempotent re-run)',
        )

    def handle(self, *args, **options):
        self._ensure_superuser()
        if options['flush']:
            self._flush()
        self._ensure_project()
        self._ensure_post()
        self.stdout.write(self.style.SUCCESS('\n✔ Demo data ready.'))
        self.stdout.write('  Admin: /admin  (credentials below)')

    # ------------------------------------------------------------------ #

    def _ensure_superuser(self):
        User = get_user_model()
        username = os.getenv('SEED_ADMIN_USER', 'admin')
        email = os.getenv('SEED_ADMIN_EMAIL', 'admin@festchuk.dev')
        password = os.getenv('SEED_ADMIN_PASSWORD', 'festchuk-dev-2026')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(
                f'• Superuser "{username}" already exists — skipping.'
            ))
            return

        User.objects.create_superuser(username, email, password)
        self.stdout.write(self.style.SUCCESS(
            f'• Created superuser "{username}"'
            f' (email={email})'
        ))
        if not os.getenv('SEED_ADMIN_PASSWORD'):
            self.stdout.write(self.style.WARNING(
                '  ⚠ Password set to dev default '
                f'"{password}" — change it for anything non-local.'
            ))

    def _flush(self):
        p = Project.objects.filter(slug=DEMO_PROJECT_SLUG).delete()
        b = Post.objects.filter(slug=DEMO_POST_SLUG).delete()
        self.stdout.write(self.style.WARNING(
            f'• Flushed demo data: project={bool(p[0])}, post={bool(b[0])}'
        ))

    def _ensure_project(self):
        project, created = Project.objects.get_or_create(
            slug=DEMO_PROJECT_SLUG,
            defaults={
                'title_ru': DEMO_PROJECT_TITLE,
                'summary_ru': 'AI-платформа мониторинга сетевой инфраструктуры в реальном времени.',
                'description_ru': PROJECT_README.split('\n', 1)[-1],
                'github_url': 'https://github.com/Inna949Festchuk/neural-grid',
                'demo_url': '',
                'technologies': [
                    'Next.js', 'Django', 'Python', 'Celery',
                    'PostgreSQL', 'PyTorch', 'WebSocket',
                ],
                'readme_ru': PROJECT_README,
                'visibility': Project.Visibility.PUBLIC,
                'is_featured': True,
                'order': 1,
            },
        )
        self.stdout.write(
            self.style.SUCCESS('• Project created: ' + project.title_ru)
            if created else
            self.style.WARNING('• Project exists — skipping: ' + project.title_ru)
        )

    def _ensure_post(self):
        post, created = Post.objects.get_or_create(
            slug=DEMO_POST_SLUG,
            defaults={
                'title_ru': DEMO_POST_TITLE,
                'excerpt_ru': 'RAG без fine-tuning: pgvector, bge-m3, Qwen — от чанкинга до retrieval.',
                'content_ru': POST_CONTENT,
                'tags': ['ai', 'rag', 'pgvector', 'django', 'python'],
                'status': Post.Status.PUBLISHED,
            },
        )
        self.stdout.write(
            self.style.SUCCESS('• Post created: ' + post.title_ru)
            if created else
            self.style.WARNING('• Post exists — skipping: ' + post.title_ru)
        )
