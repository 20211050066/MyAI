"""嵌入服务"""
import logging
from typing import List

from config import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """统一的 Embedding 服务，支持普通嵌入和上下文增强嵌入"""

    def __init__(self):
        self._model = None
        self.dimension = config.embedding.dimension

    def _get_model(self):
        if self._model is None:
            from langchain_community.embeddings import DashScopeEmbeddings
            self._model = DashScopeEmbeddings(model=config.embedding.model_name)
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """将单个查询文本转为向量"""
        model = self._get_model()
        if len(text) > config.embedding.max_chars:
            text = text[:config.embedding.max_chars]
        return model.embed_query(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """批量将文档转为向量"""
        model = self._get_model()
        truncated = [t[:config.embedding.max_chars] for t in texts]
        return model.embed_documents(truncated)

    def embed_with_context(self, content: str, context: str) -> List[float]:
        """上下文增强 Embedding（参考 Anthropic Contextual Retrieval 论文）"""
        enhanced = f"{context}\n---\n{content}"
        return self.embed_query(enhanced)
