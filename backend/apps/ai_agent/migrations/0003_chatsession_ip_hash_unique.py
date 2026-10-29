"""
Make ChatSession.ip_hash unique.

Views resolve a visitor's session with `get_or_create(ip_hash=...)`. Without a
database-level unique constraint that is not atomic: two concurrent requests
(React 18 StrictMode mounts effects twice in dev) both see no row and both
insert, after which every later lookup dies with MultipleObjectsReturned and
the chat silently stops responding.

Existing duplicates are collapsed first — keeping the most recently active
session — so the migration also succeeds on databases that already raced.
"""
from django.db import migrations, models
from django.db.models import Count


def collapse_duplicate_ip_hashes(apps, schema_editor):
    ChatSession = apps.get_model('ai_agent', 'ChatSession')
    duplicates = (
        ChatSession.objects.values('ip_hash')
        .annotate(n=Count('ip_hash'))
        .filter(n__gt=1)
    )
    for row in duplicates:
        keeper = (
            ChatSession.objects.filter(ip_hash=row['ip_hash'])
            .order_by('-last_active_at', '-created_at')
            .first()
        )
        # ChatMessage rows cascade with their session.
        ChatSession.objects.filter(ip_hash=row['ip_hash']).exclude(pk=keeper.pk).delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('ai_agent', '0002_documentembedding_embedding'),
    ]

    operations = [
        migrations.RunPython(collapse_duplicate_ip_hashes, reverse_noop),
        migrations.AlterField(
            model_name='chatsession',
            name='ip_hash',
            field=models.CharField(
                db_index=True,
                max_length=64,
                unique=True,
                verbose_name='IP Hash',
            ),
        ),
    ]
