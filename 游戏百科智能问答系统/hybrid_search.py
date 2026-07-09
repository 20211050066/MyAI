"""混合搜索编排服务"""
import hashlib
import json
import logging
from typing import List, Tuple

from config import config
from fulltext_search import FulltextSearchService
from vector_search import VectorSearchService
from reranker import RerankService

logger = logging.getLogger(__name__)


class HybridSearchService:
    """混合搜索编排
    流程：Query Rewrite -> 双路召回 -> RRF 融合 -> Rerank -> 去重截断
    """

    def __init__(self):
        self.vector_search = VectorSearchService()
        self.fulltext_search = FulltextSearchService()
        self.reranker = RerankService()

    def search(self, query: str, top_k: int = None) -> List[dict]:
        """执行混合搜索全流程"""
        if top_k is None:
            top_k = config.search.final_top_k

        # Step 1: Query Rewrite
        queries = self._query_rewrite(query)

        # Step 2: 双路召回
        all_results = []
        for q in queries:
            all_results.append(self.vector_search.search(q))
            all_results.append(self.fulltext_search.search(q))

        # Step 3: RRF 融合排序
        rrf_fused = self._rrf_fusion(all_results)

        # Step 4: Rerank 精排
        reranked = self.reranker.rerank(query, rrf_fused, top_k * 2)

        # Step 5: 去重 + 截断
        final = self._dedup_and_truncate(reranked, top_k)
        return [{"chunk_id": r[0], "content": r[1], "score": r[2], "document_id": r[3]} for r in final]

    def _query_rewrite(self, query: str) -> List[str]:
        """Query Rewrite：使用 LLM 生成多个检索变体（带 Redis 缓存）"""
        variants = [query]
        cache_key = "hybrid:query:" + hashlib.md5(query.encode()).hexdigest()
        r = None
        try:
            from db_pool import get_redis
            r = get_redis()
            if r:
                cached = r.get(cache_key)
                if cached:
                    return json.loads(cached)
        except Exception:
            pass

        try:
            from langchain_community.chat_models import ChatTongyi
            chat = ChatTongyi(model=config.llm.rewrite_model, temperature=0.3)
            prompt = f"请将以下搜索查询改写成{config.search.rewrite_variant_count}个不同措辞的检索变体，只输出变体，每行一个，不要编号：\n{query}"
            resp = chat.invoke(prompt)
            lines = [line.strip() for line in resp.content.strip().split("\n") if line.strip() and len(line.strip()) > 3]
            if len(lines) >= config.search.rewrite_variant_count:
                variants = [query] + lines[:config.search.rewrite_variant_count]
        except Exception as e:
            logger.warning("Query Rewrite 失败，使用原始查询: %s", e)

        try:
            if r:
                r.setex(cache_key, 600, json.dumps(variants))
        except Exception:
            pass
        return variants

    def _rrf_fusion(self, result_lists: List[List[Tuple]]) -> List[Tuple[int, str, float, int]]:
        """RRF（Reciprocal Rank Fusion）多路召回融合"""
        scores = {}
        details = {}
        for rank_list in result_lists:
            for rank, item in enumerate(rank_list):
                cid = item[0]
                scores[cid] = scores.get(cid, 0.0) + 1.0 / (config.search.rrf_constant_k + rank + 1)
                if cid not in details:
                    details[cid] = item
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [(details[cid][0], details[cid][1], scores[cid], details[cid][3]) for cid in sorted_ids]

    def _dedup_and_truncate(self, results: List[Tuple], top_k: int) -> List[Tuple]:
        """按文档去重，每篇文档最多保留 max_chunks_per_doc 个片段"""
        seen_docs = {}
        final = []
        for r in results:
            doc_id = r[3]
            count = seen_docs.get(doc_id, 0)
            if count < config.search.max_chunks_per_doc:
                seen_docs[doc_id] = count + 1
                final.append(r)
        return final[:top_k]
