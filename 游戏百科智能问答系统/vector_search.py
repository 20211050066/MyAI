"""向量搜索服务"""
import logging
import math
from typing import List, Tuple

from config import config
from db_pool import get_pg_conn
from embeddings import EmbeddingService

logger = logging.getLogger(__name__)


class VectorSearchService:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def search(self, query: str, top_k: int = None) -> List[Tuple[int, str, float, int]]:
        if top_k is None:
            top_k = config.search.vector_top_k
        query_vec = self.embedding_service.embed_query(query)

        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, content, embedding, document_id
                    FROM document_chunks
                    WHERE embedding IS NOT NULL
                """)
                rows = cur.fetchall()

        # 计算余弦相似度
        scored = []
        for r in rows:
            chunk_id, content, db_vec, doc_id = r
            if db_vec is None or len(db_vec) != len(query_vec):
                continue
            score = self._cosine_similarity(query_vec, db_vec)
            scored.append((chunk_id, content, score, doc_id))

        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
