"""
Заполняет реальным контентом портфолио: статьи Хабра + репозитории GitHub.

Использование:
    python manage.py seed_portfolio                # идемпотентно
    python manage.py seed_portfolio --flush        # сначала удалить ВСЕ статьи/проекты
    python manage.py seed_portfolio --no-readme    # не скачивать README с GitHub
    python manage.py seed_portfolio --no-images    # не скачивать обложки/превью
    python manage.py seed_portfolio --no-embed     # не генерировать RAG-эмбеддинги

Поведение:
- Удаляет демо-записи seed_demo (проект neural-grid, статью rag-assistant-...).
- Статьи: полный текст из data/articles/*.md, EN-поля пусты (фоллбек на RU).
- Проекты: все не-форки GitHub, README скачивается с raw.githubusercontent.com.
- Обложки статей: og:image с habr.com скачивается и сохраняется локально
  в MEDIA_ROOT/blog/covers/ (ссылки на Хабр/GitHub в браузере не работают —
  хотлинлинг и CORS/CSP, поэтому картинки храним у себя).
- Превью проектов: изображение из корня репозитория (поле cover_image) или
  первая картинка из README; сохраняется в MEDIA_ROOT/projects/previews/.
- После создания генерируются эмбеддинги для RAG (AI-ассистент).
"""
import hashlib
import io
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, urlparse

import requests
from django.core.files.base import ContentFile
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
USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/120.0 Safari/537.36'
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024          # 8 МБ на картинку
COVER_MAX_SIDE = 1600                      # обложки статей
PREVIEW_MAX_SIDE = 1200                    # превью проектов
ALLOWED_IMAGE_EXT = {'.jpg', '.jpeg', '.png', '.webp'}
# Разрешённые для скачивания домены (защита от SSRF при чужих URL).
ALLOWED_DOWNLOAD_HOST_SUFFIXES = (
    'habrastorage.org',
    'habr.com',
    'githubusercontent.com',
    'github.com',
)

_MD_IMG_RE = re.compile(
    r'!\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+["\'][^"\']*["\'])?\s*\)'
)


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


# --------------------------------------------------------------------------- #
# Скачивание и сохранение изображений
# --------------------------------------------------------------------------- #

def _host_allowed(url: str) -> bool:
    host = (urlparse(url).hostname or '').lower()
    return any(
        host == suffix or host.endswith('.' + suffix)
        for suffix in ALLOWED_DOWNLOAD_HOST_SUFFIXES
    )


def download_image(url: str) -> bytes:
    """Скачивает картинку (best-effort: b'' при любой ошибке)."""
    if not url or not url.startswith(('http://', 'https://')) or not _host_allowed(url):
        return b''
    try:
        resp = requests.get(
            url, timeout=REQUEST_TIMEOUT, headers={'User-Agent': USER_AGENT},
            stream=True,
        )
        if resp.status_code != 200:
            return b''
        declared = int(resp.headers.get('Content-Length') or 0)
        if declared > MAX_IMAGE_BYTES:
            return b''
        data = resp.content[:MAX_IMAGE_BYTES + 1]
        return data if len(data) <= MAX_IMAGE_BYTES else b''
    except (requests.RequestException, ValueError) as exc:
        logger.debug('Image download error %s: %s', url, exc)
        return b''


def normalize_image(data: bytes, max_side: int):
    """Валидация, конвертация в JPEG/PNG/WEBP, ресайз до max_side.
    Возвращает (bytes, ext) или None, если данные не картинка."""
    if not data:
        return None
    try:
        from PIL import Image
    except ImportError:  # Pillow есть в requirements; fallback без ресайза
        return data, ('.jpg' if _looks_jpeg(data) else '.png')

    try:
        img = Image.open(io.BytesIO(data))
        img.load()
    except Exception:  # noqa: BLE001 — битые данные
        return None

    if img.width < 64 or img.height < 64:  # иконки/бейджи shields.io — не годятся
        return None

    fmt = (img.format or '').upper()
    if fmt not in ('JPEG', 'PNG', 'WEBP'):
        img = img.convert('RGB')
        fmt = 'JPEG'

    img.thumbnail((max_side, max_side), Image.LANCZOS)

    buf = io.BytesIO()
    if fmt == 'WEBP':
        img.save(buf, 'WEBP', quality=85)
        ext = '.webp'
    elif fmt == 'PNG':
        img.save(buf, 'PNG', optimize=True)
        ext = '.png'
    else:
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        img.save(buf, 'JPEG', quality=85, optimize=True)
        ext = '.jpg'
    out = buf.getvalue()
    return (out, ext) if out else None


def _looks_jpeg(data: bytes) -> bool:
    return data[:3] == b'\xff\xd8\xff'


def _storage_exists(file_field) -> bool:
    """True, если файл field реально лежит в хранилище (или проверку
    сделать нельзя — считаем, что есть)."""
    if not file_field or not file_field.name:
        return False
    try:
        return file_field.storage.exists(file_field.name)
    except NotImplementedError:
        return True


def attach_image(obj, field_name: str, stem: str, url: str,
                 max_side: int, force: bool) -> bool:
    """Скачивает url, нормализует и сохраняет в ImageField obj.<field_name>.
    Идемпотентно: пропускает, если файл с тем же stem уже лежит на диске
    (кроме --force-images). Возвращает True, если изображение обновлено."""
    if not url:
        return False
    current = getattr(obj, field_name)
    if not force and current and current.name.startswith(stem):
        try:
            if current.storage.exists(current.name):
                return False
        except NotImplementedError:
            pass
    normalized = normalize_image(download_image(url), max_side)
    if not normalized:
        return False
    out, ext = normalized
    name = f'{stem}{ext}'
    # старое изображение (например, с другим расширением) удаляем за собой
    if current and current.name and current.name != name:
        current.delete(save=False)
    storage = obj._meta.get_field(field_name).storage
    path = storage.save(name, ContentFile(out))
    setattr(obj, field_name, path)
    obj.save(update_fields=[field_name])
    return True


def habr_cover_url(article_url: str) -> str:
    """og:image страницы статьи на Хабре ('' при неудаче)."""
    try:
        resp = requests.get(
            article_url, timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': USER_AGENT},
        )
        if resp.status_code != 200:
            return ''
    except requests.RequestException as exc:
        logger.debug('Habr page error %s: %s', article_url, exc)
        return ''
    m = re.search(
        r'<meta\s+property="og:image"\s+content="([^"]+)"', resp.text
    ) or re.search(
        r'<meta\s+content="([^"]+)"\s+property="og:image"', resp.text
    )
    return m.group(1) if m else ''


def fetch_habr_article(article_url: str) -> str:
    """Скачивает HTML-контент статьи с Хабра и конвертирует в markdown.
    
    Возвращает markdown-строку с абсолютными ссылками на картинки (hadrastorage.org).
    При ошибке возвращает пустую строку.
    """
    try:
        import html2text
        from bs4 import BeautifulSoup
        
        resp = requests.get(
            article_url, timeout=REQUEST_TIMEOUT,
            headers={'User-Agent': USER_AGENT},
        )
        if resp.status_code != 200:
            logger.warning('Habr article fetch error %s: HTTP %s', article_url, resp.status_code)
            return ''
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        # Контент статьи находится в div с классом article-body
        article_div = soup.find('div', class_='article-body')
        if not article_div:
            # Попробовать альтернативный селектор
            article_div = soup.find('div', class_='content')
        if not article_div:
            logger.warning('Habr article body not found: %s', article_url)
            return ''
        
        # Исправить URL картинок: Habr обрезает расширение в src, добавляем .png
        for img in article_div.find_all('img'):
            src = img.get('src', '')
            if src and 'habrastorage.org' in src and not src.endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                img['src'] = src + '.png'
        
        # Конвертировать HTML в markdown
        h = html2text.HTML2Text()
        h.body_width = 0  # Не переносить строки
        h.protect_links = True
        h.wrap_links = False
        h.images_to_alt = False  # Оставлять src, не заменять на alt
        h.ignore_images = False
        h.ignore_emphasis = False
        h.mark_code = False
        h.skip_internal_links = False
        h.single_line_break = False
        
        markdown = h.handle(str(article_div))
        
        # Убрать первый H1 (заголовок статьи хранится отдельно)
        markdown = _strip_h1(markdown)
        
        return markdown.strip()
    
    except ImportError:
        logger.warning('html2text not installed, skipping Habr article fetch')
        return ''
    except Exception as exc:
        logger.warning('Habr article fetch error %s: %s', article_url, exc)
        return ''


def _is_badge(src: str) -> bool:
    low = src.lower()
    return 'shields.io' in low or '/badge/' in low or low.endswith('.svg')


def repo_image_candidates(readme: str, github_url: str, branch: str,
                          declared: str) -> list:
    """URL-кандидаты картинки-обложки проекта: объявленная, из README
    (абсолютные и относительные к репозиторию)."""
    path = github_url.rstrip('/').replace('https://github.com/', '')
    base = f'https://raw.githubusercontent.com/{path}/{branch}/'
    urls = []
    if declared:
        if declared.startswith('http'):
            urls.append(declared)
        else:
            urls.append(base + quote(declared.lstrip('/')))
    for m in _MD_IMG_RE.finditer(readme or ''):
        src = m.group(1)
        if _is_badge(src):
            continue
        if src.startswith('http'):
            urls.append(src)
        elif not src.startswith('/'):
            urls.append(base + quote(src))
    # dedupe preserving order
    return list(dict.fromkeys(u for u in urls if u))


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
            '--no-images', action='store_true',
            help='Не скачивать обложки статей и превью проектов',
        )
        parser.add_argument(
            '--force-images', action='store_true',
            help='Перекачать изображения даже если они уже сохранены',
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

        posts = self._seed_articles(opts)
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

    def _seed_articles(self, opts) -> list:
        created = 0
        images_ok = 0
        for article in ARTICLES:
            # Сначала пытаемся скачать контент с Хабра (если есть habr_url)
            content = ''
            source = 'local'
            if article.get('habr_url') and not opts.get('no_readme'):
                content = fetch_habr_article(article['habr_url'])
                if content:
                    source = 'habr'
            
            # Если не удалось скачать с Хабра — читаем локальный файл
            if not content:
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

            marker = f' [{source}]'
            if not opts['no_images']:
                stem = hashlib.sha1(
                    (article.get('habr_url') or article['slug']).encode()
                ).hexdigest()[:12]
                cur = post.cover_image
                have_file = False
                if cur and cur.name:
                    try:
                        have_file = cur.storage.exists(cur.name)
                    except NotImplementedError:
                        have_file = True
                if have_file and not opts['force_images']:
                    marker = ' cover ✓(cached)'
                elif article.get('habr_url'):
                    url = habr_cover_url(article['habr_url'])
                    if attach_image(post, 'cover_image', stem, url,
                                    COVER_MAX_SIDE, opts['force_images']):
                        images_ok += 1
                        marker = ' cover ✓'
                    elif url:
                        marker = ' cover —'
                    else:
                        marker = ' cover ✗(no og:image)'

            self.stdout.write(
                f'• Article: {post.title_ru} ({len(content):,} chars){marker}'
            )
        self.stdout.write(self.style.SUCCESS(
            f'• Articles: {created} created, {len(ARTICLES) - created} updated, '
            f'{images_ok} covers downloaded'
        ))
        return list(Post.objects.filter(slug__in=[a['slug'] for a in ARTICLES]))

    def _seed_projects(self, opts) -> list:
        slugs = []
        images_ok = 0
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
            if not opts['no_images']:
                stem = hashlib.sha1(
                    item['github_url'].encode()
                ).hexdigest()[:12]
                candidates = repo_image_candidates(
                    readme, item['github_url'], item['branch'],
                    item.get('cover_image', ''),
                )
                saved = False
                for url in candidates:
                    if attach_image(project, 'image_preview', stem, url,
                                    PREVIEW_MAX_SIDE, opts['force_images']):
                        saved = True
                        break
                    # файл уже на месте (идемпотентность) — тоже успех
                    cur = project.image_preview
                    if cur and cur.name.startswith(stem):
                        saved = True
                        break
                # Карточки проектов рендерят cover_image, а не image_preview —
                # дублируем то же превью в cover_image.
                if saved and project.image_preview:
                    src = project.image_preview
                    try:
                        exists = src.storage.exists(src.name)
                    except NotImplementedError:
                        exists = False
                    dst = project.cover_image
                    need_copy = (
                        opts['force_images'] or not exists
                        or not dst or not dst.name
                        or not _storage_exists(dst)
                        or os.path.splitext(dst.name)[1]
                        != os.path.splitext(src.name)[1]
                    )
                    if need_copy:
                        if dst and dst.name:
                            dst.delete(save=False)
                        cname = f'{stem}{os.path.splitext(src.name)[1]}'
                        path = project._meta.get_field(
                            'cover_image').storage.save(
                            cname, ContentFile(src.open('rb').read()))
                        project.cover_image = path
                        project.save(update_fields=['cover_image'])
                marker += ' img ✓' if saved else (' img —' if candidates else '')
            featured = ' ★' if item['is_featured'] else ''
            if 'img ✓' in marker:
                images_ok += 1
            self.stdout.write(f'• Project: {item["name"]}{featured} {marker}')

        self.stdout.write(self.style.SUCCESS(
            f'• Project previews downloaded: {images_ok}'
        ))
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
