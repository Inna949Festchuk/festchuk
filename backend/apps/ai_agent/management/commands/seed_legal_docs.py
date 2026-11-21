"""
Bootstrap the 152-FZ personal-data law into the ``LegalDocument`` model.

The plain-text source lives in the repo at ``apps/ai_agent/legal/`` so the
document can be created on any host without external dependencies.

After the first run the Django Admin (Нормативные документы) becomes the
source of truth: this command will NOT overwrite an existing document's
text or re-run the paid embedding. Re-index the RAG explicitly via the
admin action «Проиндексировать в RAG» (``embed_legal_document`` task).
"""
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.ai_agent.models import DocumentEmbedding, LegalDocument
from apps.ai_agent.services.rag import RAGService

# Stable lookup key for the document (Admin edits happen under this row).
LEGAL_CODE = 'fz-152'
LEGAL_FILE = Path(__file__).resolve().parents[2] / 'legal' / 'fz_152_2026.txt'
TITLE = 'Федеральный закон № 152-ФЗ «О персональных данных» (ред. от 26.07.2026)'


class Command(BaseCommand):
    help = 'Bootstrap the 152-FZ law into LegalDocument and (first run only) the RAG index.'

    def handle(self, *args, **options):
        if not LEGAL_FILE.exists():
            self.stderr.write(f'ERROR: legal text not found: {LEGAL_FILE}')
            return

        text = LEGAL_FILE.read_text(encoding='utf-8')
        if not text.strip():
            self.stderr.write('ERROR: legal text is empty')
            return

        doc, created = LegalDocument.objects.get_or_create(
            code=LEGAL_CODE,
            defaults={'title': TITLE, 'text': text, 'is_active': True},
        )

        if not created:
            self.stdout.write(self.style.WARNING(
                f'Document {LEGAL_CODE} already exists — leaving its text and '
                'RAG index untouched. Edit in Admin and re-index via the '
                '«Проиндексировать в RAG» action when needed.'
            ))
            return

        self.stdout.write(f'Created LegalDocument {LEGAL_CODE} ({len(text)} chars).')

        existing = DocumentEmbedding.objects.filter(
            source_type='legal', source_id=doc.pk
        ).count()
        if existing:
            # Index already present (e.g. bootstrapped earlier under the old
            # surrogate source_id=1 which coincides with this pk) — skip the
            # paid re-embedding.
            self.stdout.write(self.style.WARNING(
                f'RAG index already has {existing} chunks for legal:{doc.pk} — '
                'skipping paid re-embedding.'
            ))
            return

        self.stdout.write('Embedding into RAG ...')
        rag = RAGService()
        stored = rag.embed_document(
            text=doc.text,
            source_type=DocumentEmbedding.SourceType.LEGAL,
            source_id=doc.pk,
            metadata={'title': doc.title},
        )
        self.stdout.write(self.style.SUCCESS(
            f'Stored {stored} chunks for legal:{doc.pk}.'
        ))
