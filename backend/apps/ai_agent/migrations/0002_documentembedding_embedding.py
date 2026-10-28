"""
Add pgvector support: CREATE EXTENSION vector + embedding column.

The RAG service (apps/ai_agent/services/rag.py) stores bge-m3 embeddings
(1024 dims) via raw SQL and queries them with the cosine operator `<=>`.
"""
import pgvector.django
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ai_agent', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql='CREATE EXTENSION IF NOT EXISTS vector;',
            reverse_sql='DROP EXTENSION IF EXISTS vector;',
        ),
        migrations.AddField(
            model_name='documentembedding',
            name='embedding',
            field=pgvector.django.VectorField(dimensions=1024),
        ),
    ]