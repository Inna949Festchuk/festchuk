"""
RAG (Retrieval-Augmented Generation) service.

Handles document chunking, embedding storage/retrieval via pgvector,
and context assembly for the AI agent.
"""
import logging
import math
import re

from django.conf import settings
from django.db import connection

from .router_ai import RouterAIClient

logger = logging.getLogger(__name__)

# Embedding dimension — must match the model
EMBEDDING_DIMENSION = 1024  # bge-m3


def _chunk_text(text: str, chunk_size: int = 800, overlap: int = 100) -> list[str]:
    """
    Split text into overlapping chunks.

    Args:
        text: Input text
        chunk_size: Approximate characters per chunk (~200-300 tokens)
        overlap: Characters to overlap between chunks

    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []

    # Normalize whitespace
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size

        # Try to break at paragraph boundary
        if end < text_len:
            # Look for paragraph break in the next 200 chars
            paragraph_break = text.find('\n\n', start, end + 200)
            if paragraph_break > start + chunk_size // 2:
                end = paragraph_break

            # If no paragraph break, try sentence break
            if end == start + chunk_size:
                sentence_break = text.rfind('. ', start, end)
                if sentence_break > start + chunk_size // 2:
                    end = sentence_break + 1

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap

    return chunks


class RAGService:
    """
    RAG service for document embedding and retrieval.
    """

    def __init__(self):
        self.client = RouterAIClient()

    def embed_document(
        self,
        text: str,
        source_type: str,
        source_id: int,
        metadata: dict | None = None,
    ) -> int:
        """
        Chunk a document, generate embeddings, and store in pgvector.

        Returns:
            Number of chunks stored
        """
        from apps.ai_agent.models import DocumentEmbedding

        # Clear existing embeddings for this source
        DocumentEmbedding.objects.filter(
            source_type=source_type,
            source_id=source_id,
        ).delete()

        # Chunk the text
        chunks = _chunk_text(text)
        if not chunks:
            return 0

        metadata = metadata or {}
        stored = 0

        # Process in batches (RouterAI may have batch limits)
        batch_size = 10
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            try:
                embeddings = self.client.embeddings(batch)
            except Exception as e:
                logger.error(f"Embedding error for {source_type}:{source_id}: {e}")
                break

            for j, (chunk, embedding) in enumerate(zip(batch, embeddings)):
                chunk_index = i + j
                # Store via raw SQL for pgvector
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO ai_agent_documentembedding
                        (source_type, source_id, chunk_index, chunk_text, metadata,
                         embedding, created_at, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, NOW(), NOW())
                        ON CONFLICT (source_type, source_id, chunk_index)
                        DO UPDATE SET
                            chunk_text = EXCLUDED.chunk_text,
                            metadata = EXCLUDED.metadata,
                            embedding = EXCLUDED.embedding,
                            updated_at = NOW()
                        """,
                        [
                            source_type,
                            source_id,
                            chunk_index,
                            chunk,
                            self._json_dumps(metadata),
                            self._vector_literal(embedding),
                        ],
                    )
                stored += 1

        logger.info(f"Stored {stored} embeddings for {source_type}:{source_id}")
        return stored

    def search_similar(
        self,
        query: str,
        top_k: int | None = None,
        source_type: str | None = None,
    ) -> list[dict]:
        """
        Search for similar document chunks using vector similarity.

        Returns:
            List of dicts with 'chunk_text', 'metadata', 'score', 'source_type', 'source_id'
        """
        from apps.ai_agent.models import DocumentEmbedding

        top_k = top_k or settings.RAG_TOP_K

        try:
            query_embedding = self.client.embeddings([query])[0]
        except Exception as e:
            logger.error(f"Query embedding error: {e}")
            return []

        # Build filter
        where_clause = ""
        params: list = []
        if source_type:
            where_clause = "WHERE source_type = %s"
            params.append(source_type)

        vector_literal = self._vector_literal(query_embedding)

        with connection.cursor() as cursor:
            query = f"""
                SELECT
                    chunk_text,
                    metadata,
                    source_type,
                    source_id,
                    1 - (embedding <=> %s) AS similarity
                FROM ai_agent_documentembedding
                {where_clause}
                ORDER BY embedding <=> %s
                LIMIT %s
            """
            cursor.execute(query, [vector_literal, vector_literal, top_k] + params)
            rows = cursor.fetchall()

        results = []
        for row in rows:
            chunk_text, metadata_json, src_type, src_id, similarity = row
            import json
            metadata = json.loads(metadata_json) if isinstance(metadata_json, str) else metadata_json
            results.append({
                'chunk_text': chunk_text,
                'metadata': metadata,
                'source_type': src_type,
                'source_id': src_id,
                'score': float(similarity),
            })

        return results

    def build_context(self, chunks: list[dict]) -> str:
        """
        Assemble retrieved chunks into a context string for the LLM prompt.
        """
        if not chunks:
            return ""

        parts = []
        for i, chunk in enumerate(chunks, 1):
            source_label = chunk['source_type']
            meta_title = chunk['metadata'].get('title', '')
            header = f"[{i}] {source_label}"
            if meta_title:
                header += f": {meta_title}"

            parts.append(f"{header}\n{chunk['chunk_text']}")

        return "\n\n---\n\n".join(parts)

    # --- Helpers ---

    @staticmethod
    def _vector_literal(embedding: list[float]) -> str:
        """Convert embedding list to pgvector literal string."""
        return '[' + ','.join(str(x) for x in embedding) + ']'

    @staticmethod
    def _json_dumps(obj: dict) -> str:
        import json
        return json.dumps(obj, ensure_ascii=False)
