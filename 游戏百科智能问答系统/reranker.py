"""重排序服务（Rerank）"""
import logging
from typing import List, Tuple

from config import config

logger = logging.getLogger(__name__)


class RerankService:
    """重排序服务，使用智谱 Rerank API 精排"""

    def rerank(self, query: str, candidates: List[Tuple[int, str, float, int]],
               top_k: int = None) -> List[Tuple[int, str, float, int]]:
        """对候选结果进行重排序，失败时回退到原始排序"""
        if not candidates:
            return []
        if top_k is None:
            top_k = config.search.final_top_k
        try:
            return self._call_rerank_api(query, candidates, top_k)
        except Exception as e:
            logger.warning("Rerank 失败，回退到 RRF 原始排序: %s", e)
            return candidates[:top_k]

    def _call_rerank_api(self, query: str, candidates: List[Tuple],
                          top_k: int) -> List[Tuple[int, str, float, int]]:
        """调用智谱 Rerank API"""
        import httpx
        top_n = min(len(candidates), config.search.rerank_candidate_count)
        docs_to_rerank = [c[1][:config.rerank.max_chars_per_doc] for c in candidates[:top_n]]
        payload = {
            "model": config.rerank.model,
            "input": {
                "query": query,
                "documents": docs_to_rerank,
            },
            "parameters": {
                "top_n": min(top_k, len(docs_to_rerank)),
            },
        }
        headers = {
            "Authorization": f"Bearer {config.rerank.api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=config.rerank.timeout) as client:
            resp = client.post(config.rerank.api_base, json=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()
        scored = []
        for item in result.get("output", {}).get("results", []):
            idx = item.get("index", 0)
            score = item.get("relevance_score", 0.0)
            if score >= config.search.rerank_min_score:
                c = candidates[idx]
                scored.append((c[0], c[1], score, c[3]))
        scored.sort(key=lambda x: x[2], reverse=True)
        return scored[:top_k]
