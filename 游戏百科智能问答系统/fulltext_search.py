"""全文搜索服务（PostgreSQL tsvector + Jieba 分词）"""
import logging
from typing import List, Tuple

from config import config
from db_pool import get_pg_conn

logger = logging.getLogger(__name__)


class FulltextSearchService:
    """全文搜索，使用 tsvector 与 ts_query"""

    def search(self, query: str, top_k: int = None) -> List[Tuple[int, str, float, int]]:
        """全文搜索，返回列表：(chunk_id, content, score, document_id)"""
        if top_k is None:
            top_k = config.search.fulltext_top_k
        tokens = self._tokenize(query)
        tsquery = " & ".join(tokens)
        if not tsquery:
            return []
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT dc.id, dc.content,
                           ts_rank(to_tsvector('simple', dc.content), to_tsquery('simple', %s)) AS score,
                           dc.document_id
                    FROM document_chunks dc
                    WHERE to_tsvector('simple', dc.content) @@ to_tsquery('simple', %s)
                    ORDER BY score DESC
                    LIMIT %s
                """, (tsquery, tsquery, top_k))
                return [(r[0], r[1], float(r[2]), r[3]) for r in cur.fetchall()]

    def _tokenize(self, text: str) -> List[str]:
        """中文分词，优先使用 Jieba，回退到空格分词"""
        try:
            import jieba
            return [w.strip() for w in jieba.cut(text) if len(w.strip()) > 1]
        except ImportError:
            return [w.strip() for w in text.split() if len(w.strip()) > 1]
