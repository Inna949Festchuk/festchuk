"""
Заполняет реальным контентом портфолио: статьи Хабра + репозитории GitHub.

Использование:
    python manage.py seed_portfolio                # идемпотентно
    python manage.py seed_portfolio --flush        # сначала удалить ВСЕ статьи/проекты
    python manage.py seed_portfolio --no-readme    # не скачивать README с GitHub
    python manage.py seed_portfolio --no-embed     # не генерировать RAG-эмбеддинги

Поведение:
- Удаляет демо-записи seed_demo (проект neural-grid, статью rag-assistant-...).
- Статьи: полный текст из data/articles/*.md, EN-поля пусты (фоллбек на RU).
- Проекты: все не-форки GitHub, README скачивается с raw.githubusercontent.com.
- После создания генерируются эмбеддинги для RAG (AI-ассистент).
"""
import logging
import re
from datetime import datetime
from pathlib import Path

import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.dateparse import parse_date

from apps.blog.models import Post
from apps.projects.models import Project
from apps.core.data.portfolio_content import ARTICLES, PROJECTS

logger = logging.getLogger(__name__)

ARTICLES_DIR = Path(__file__).resolve().parents[2] / 'data' / 'articles'

# Демо-записи, созданные seed_demo — удаляются при каждом запуске.
DEMO_POST_SLUG = 'rag-assistant-pgvector-qwen'
DEMO_PROJECT_SLUG = 'neural-grid'

README_NAMES = ('README.md', 'readme.md', 'README.rst', 'README')
REQUEST_TIMEOUT = 20


def _strip_h1(markdown: str) -> str:
    """Убирает первый заголовок H1 (заголовок хранится отдельно в title)."""
    lines = markdown.splitlines()
    if lines and lines[0].startswith('# '):
        lines = lines[1:]
    return '\n'.join(lines).lstrip('\n')


def _make_excerpt(markdown: str, max_len: int = 480) -> str:
    """Первый содержательный абзац статьи как анонс (без markdown-разметки)."""
    parts = []
    started = False
    for line in markdown.splitlines():
        s = line.strip()
        if not s:
            if started:
                break
            continue
        if s.startswith(('#', '```', '>', '|', '-', '*', '![', '[[')):
            if started:
                break
            continue
        started = True
        parts.append(s)
    text = ' '.join(parts)
    text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)  # ссылки -> текст
    text = re.sub(r'[*_`~]', '', text)
    if len(text) > max_len:
        text = text[:max_len].rsplit(' ', 1)[0].rstrip(',') + '…'
    return text.strip()


def _readme_urls(github_url: str, branch: str) -> list:
    """Кандидатные URL README: сначала README.md по всем веткам, затем прочие имена."""
    path = github_url.rstrip('/').replace('https://github.com/', '')
    branches = list(dict.fromkeys([branch, 'main', 'master']))
    urls = [
        f'https://raw.githubusercontent.com/{path}/{b}/README.md'
        for b in branches
    ]
    urls += [
        f'https://raw.githubusercontent.com/{path}/{branches[0]}/{name}'
        for name in README_NAMES[1:]
    ]
    return urls


def fetch_readme(github_url: str, branch: str) -> str:
    """Best-effort скачивание README репозитория. '' при неудаче."""
    for url in _readme_urls(github_url, branch):
        try:
            resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            logger.debug('README fetch error %s: %s', url, exc)
            continue
        if resp.status_code == 200 and resp.text.strip():
            return resp.text
        if resp.status_code != 404:
            # 403/429 и пр. — не стоит дёргать остальные URL
            break
    return ''


class Command(BaseCommand):
    help = 'Seed real portfolio content: Habr articles + GitHub projects'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush', action='store_true',
            help='Удалить ВСЕ статьи и проекты перед заполнением',
        )
        parser.add_argument(
            '--no-readme', action='store_true',
            help='Не скачивать README с GitHub',
        )
        parser.add_argument(
            '--no-embed', action='store_true',
            help='Не генерировать RAG-эмбеддинги',
        )

    def handle(self, *args, **opts):
        self._remove_demo()

        if opts['flush']:
            n_posts, _ = Post.objects.all().delete()
            n_proj, _ = Project.objects.all().delete()
            self.stdout.write(self.style.WARNING(
                f'• Flushed: posts={n_posts}, projects={n_proj}'
            ))

        posts = self._seed_articles()
        projects = self._seed_projects(opts)

        if not opts['no_embed']:
            self._embed(posts, projects)
        else:
            self.stdout.write(self.style.WARNING('• Embeddings skipped (--no-embed)'))

        self.stdout.write(self.style.SUCCESS(
            f'\n✔ Portfolio ready: {len(posts)} articles, {len(projects)} projects'
        ))

    # ------------------------------------------------------------------ #

    def _remove_demo(self):
        from apps.ai_agent.models import DocumentEmbedding

        for model, slug, src_type in (
            (Post, DEMO_POST_SLUG, 'blog_post'),
            (Project, DEMO_PROJECT_SLUG, 'project'),
        ):
            objs = model.objects.filter(slug=slug)
            for obj in objs:
                DocumentEmbedding.objects.filter(
                    source_type=src_type, source_id=obj.pk
                ).delete()
            deleted, _ = objs.delete()
            if deleted:
                self.stdout.write(self.style.WARNING(
                    f'• Removed demo {src_type}: {slug}'
                ))

    def _seed_articles(self) -> list:
        created = 0
        for article in ARTICLES:
            path = ARTICLES_DIR / article['file']
            if not path.exists():
                self.stderr.write(self.style.ERROR(
                    f'✗ Article file not found: {path}'
                ))
                continue

            raw = path.read_text(encoding='utf-8')
            content = _strip_h1(raw)
            excerpt = _make_excerpt(content)
            published_at = timezone.make_aware(
                datetime.combine(parse_date(article['published_at']),
                                 datetime.min.time())
            )

            post, was_created = Post.objects.update_or_create(
                slug=article['slug'],
                defaults={
                    'title_ru': article['title_ru'],
                    'excerpt_ru': excerpt,
                    'content_ru': content,
                    'tags': article['tags'],
                    'status': Post.Status.PUBLISHED,
                    'published_at': published_at,
                },
            )
            created += int(was_created)
            self.stdout.write(
                f'• Article: {post.title_ru} ({len(content):,} chars)'
            )
        self.stdout.write(self.style.SUCCESS(
            f'• Articles: {created} created, {len(ARTICLES) - created} updated'
        ))
        return list(Post.objects.filter(slug__in=[a['slug'] for a in ARTICLES]))

    def _seed_projects(self, opts) -> list:
        slugs = []
        for order, item in enumerate(PROJECTS, start=1):
            readme = ''
            if not opts['no_readme']:
                readme = fetch_readme(item['github_url'], item['branch'])

            description = (item['description'] or '').strip()
            project, _ = Project.objects.update_or_create(
                github_url=item['github_url'],
                defaults={
                    'title_ru': item['name'],
                    'summary_ru': description[:500],
                    'description_ru': description,
                    'technologies': item['technologies'],
                    'is_featured': item['is_featured'],
                    'order': order,
                    'visibility': Project.Visibility.PUBLIC,
                    'readme_ru': readme,
                },
            )
            slugs.append(project.slug)
            marker = 'README ✓' if readme else 'README —'
            featured = ' ★' if item['is_featured'] else ''
            self.stdout.write(f'• Project: {item["name"]}{featured} {marker}')

        return list(Project.objects.filter(slug__in=slugs))

    def _embed(self, posts: list, projects: list):
        from apps.ai_agent.services.rag import RAGService

        rag = RAGService()
        ok, fail = 0, 0

        def _safe(fn, *a, **kw):
            nonlocal ok, fail
            try:
                fn(*a, **kw)
                ok += 1
            except Exception as exc:  # noqa: BLE001 — не роняем сид по одному документу
                fail += 1
                logger.warning('Embedding failed: %s', exc)

        for post in posts:
            if post.content_ru:
                _safe(
                    rag.embed_document,
                    text=post.content_ru,
                    source_type='blog_post',
                    source_id=post.pk,
                    metadata={'title': post.title_ru, 'tags': post.tags},
                )

        for project in projects:
            if project.readme_ru:
                _safe(
                    rag.embed_document,
                    text=project.readme_ru,
                    source_type='project',
                    source_id=project.pk,
                    metadata={
                        'title': project.title_ru,
                        'technologies': project.technologies,
                    },
                )

        self.stdout.write(self.style.SUCCESS(
            f'• Embeddings: {ok} documents ok, {fail} failed'
        ))
