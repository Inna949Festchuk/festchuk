"""
Redis-хранилище сессий чата (152-ФЗ: ПДн не держим в PostgreSQL).

Ключи:
- chat_session:{ip_hash}  — запись сессии (dict), TTL = CHAT_SESSION_TTL;
- chat_history:{session_id} — контекст диалога (list of {role, content}).
  Раньше это был кэш с фолбэком в БД, теперь — единственная копия диалога:
  срок жизни гарантирует движок Redis (TTL), а не периодическая задача.

Гонка создания: cache.add() — атомарный SETNX, та же роль, что до этого играло
уникальное ограничение БД на ip_hash (React 18 StrictMode монтирует эффект
дважды в dev и шлёт два параллельных запроса).
"""
import uuid

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


class RedisSession:
    """Сессия с интерфейсом, который ожидает AIAgent (duck-typing).

    Не модель Django: save() пишет запись в Redis и продлевает TTL.
    """

    def __init__(self, ip_hash: str, session_id: str, active_module_slug: str = ''):
        self.ip_hash = ip_hash
        self.session_id = str(session_id)
        self.active_module_slug = active_module_slug or ''

    @property
    def pk(self):
        """Совместимость с кодом, ожидавшим первичный ключ модели."""
        return self.session_id

    def _key(self) -> str:
        return f'chat_session:{self.ip_hash}'

    def touch(self):
        """Слайдующий TTL: срок хранения отсчитывается от последнего действия."""
        self.save()

    def save(self, update_fields=None):
        """Запись мала (несколько полей), поэтому пишем целиком — без merge."""
        cache.set(self._key(), {
            'session_id': self.session_id,
            'active_module_slug': self.active_module_slug,
            'created_at': timezone.now().isoformat(),
        }, settings.CHAT_SESSION_TTL)

    def __str__(self):
        return f"Session {self.session_id[:8]}..."


def _session_key(ip_hash: str) -> str:
    return f'chat_session:{ip_hash}'


def _from_record(ip_hash: str, record: dict) -> RedisSession:
    return RedisSession(
        ip_hash=ip_hash,
        session_id=record.get('session_id', str(uuid.uuid4())),
        active_module_slug=record.get('active_module_slug', ''),
    )


def resolve_session(ip_hash: str) -> tuple:
    """Вернуть ``(session, created)`` для посетителя — атомарно один раз на IP."""
    record = cache.get(_session_key(ip_hash))
    if record:
        return _from_record(ip_hash, record), False

    new = {
        'session_id': str(uuid.uuid4()),
        'active_module_slug': '',
        'created_at': timezone.now().isoformat(),
    }
    if cache.add(_session_key(ip_hash), new, settings.CHAT_SESSION_TTL):
        return _from_record(ip_hash, new), True

    # Проиграли гонку: запись победителя уже закоммичена
    record = cache.get(_session_key(ip_hash))
    if record:
        return _from_record(ip_hash, record), False
    # Ключ исчез между add и get (вытеснение) — пробуем создать заново
    if cache.add(_session_key(ip_hash), new, settings.CHAT_SESSION_TTL):
        return _from_record(ip_hash, new), True
    return _from_record(ip_hash, new), False


def verify_session(ip_hash: str, session_id: str) -> RedisSession | None:
    """Сессия должна принадлежать этому IP; чужой/протухший ID → None (404)."""
    record = cache.get(_session_key(ip_hash))
    if record and record.get('session_id') == str(session_id):
        return _from_record(ip_hash, record)
    return None


def delete_session(ip_hash: str) -> bool:
    """«Право на удаление» (152-ФЗ): сессия и история диалога удаляются сразу."""
    record = cache.get(_session_key(ip_hash))
    cache.delete(_session_key(ip_hash))
    if record:
        cache.delete(f"chat_history:{record.get('session_id', '')}")
    return record is not None
