"""
MARS — Long-term Vector Memory via Convex.

Architecture:
  - Embeddings: openai/text-embedding-3-small (via OpenRouter)
  - Vector store: Convex Vector Search
  - Index name: by_embedding

Memory policy:
  - STORE: Synthesized answers with quality_score >= threshold
  - RETRIEVE: Before ResearchAgent runs (inject past similar research)
  - PURGE: Metadata TTL filter (90 days)
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from convex import ConvexClient
from openai import OpenAI
from backend.config.settings import settings

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "openai/text-embedding-3-small"


class LongTermMemory:
    """
    Convex-backed semantic memory for MARS research results.
    """

    def __init__(self, convex_url: Optional[str] = None):
        self.url = convex_url or settings.convex_url
        self._client = None
        self._openai_client = None

        if not self.url:
            logger.warning("Convex URL not configured. Long-term memory will be a no-op.")

    def _ensure_initialized(self) -> bool:
        """Lazy-initialize clients."""
        if self._client and self._openai_client:
            return True
        
        if not self.url:
            return False

        try:
            self._client = ConvexClient(self.url)
            self._openai_client = OpenAI(
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
            )
            return True
        except Exception as exc:
            logger.error("Failed to initialize LongTermMemory clients: %s", exc)
            return False

    def _get_embedding(self, text: str) -> List[float]:
        """Fetch embedding from OpenRouter."""
        response = self._openai_client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text.replace("\n", " ")
        )
        return response.data[0].embedding

    def store(
        self,
        session_id: str,
        query: str,
        content: str,
        quality_score: float,
        metadata: Optional[dict] = None,
    ) -> None:
        """Store a research result in Convex vector memory."""
        if quality_score < settings.quality_threshold:
            return

        if not self._ensure_initialized():
            return

        try:
            embedding = self._get_embedding(content)
            
            entry = {
                "content": content[:2000],
                "embedding": embedding,
                "quality_score": float(quality_score),
                "stored_at": datetime.utcnow().isoformat(),
                "ttl_expires": (
                    datetime.utcnow() + timedelta(days=settings.memory_ttl_days)
                ).isoformat(),
            }

            self._client.mutation("memory:store", entry)
            logger.info("Stored memory snippet in Convex (score: %.2f)", quality_score)
        except Exception as exc:
            logger.warning("Failed to store memory in Convex: %s", exc)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[str]:
        """Retrieve semantically similar past research results from Convex."""
        if not self._ensure_initialized():
            return []

        k = top_k or settings.memory_top_k
        try:
            embedding = self._get_embedding(query)
            
            # Call the Convex Action that performs the vector search
            results = self._client.action("memory:search", {
                "embedding": embedding,
                "topK": k
            })

            if not results:
                return []

            # Filter out expired entries
            now = datetime.utcnow().isoformat()
            valid = [
                r["content"] for r in results
                if r.get("ttl_expires", "9999") > now
            ]

            logger.info("Retrieved %d memory matches from Convex", len(valid))
            return valid

        except Exception as exc:
            logger.warning("Memory retrieve from Convex failed: %s", exc)
            return []

    def purge_expired(self) -> int:
        """Placeholder for periodic purge logic. Convex handles deletions via mutations."""
        return 0
