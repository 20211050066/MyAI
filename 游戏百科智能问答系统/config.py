"""全局配置模块"""
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class PostgreSQLConfig:
    """PostgreSQL 连接配置"""
    host: str = os.getenv("PG_HOST", "localhost")
    port: int = int(os.getenv("PG_PORT", "5432"))
    dbname: str = os.getenv("PG_DBNAME", "game_wiki")
    user: str = os.getenv("PG_USER", "postgres")
    password: str = os.getenv("PG_PASSWORD", "123123zfy")
    min_conn: int = int(os.getenv("PG_MIN_CONN", "2"))
    max_conn: int = int(os.getenv("PG_MAX_CONN", "10"))

    @property
    def dsn(self) -> str:
        return f"host={self.host} port={self.port} dbname={self.dbname} user={self.user} password={self.password}"

@dataclass
class RedisConfig:
    """Redis 连接配置"""
    host: str = os.getenv("REDIS_HOST", "localhost")
    port: int = int(os.getenv("REDIS_PORT", "6379"))
    db: int = int(os.getenv("REDIS_DB", "0"))
    password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    decode_responses: bool = True
    session_ttl: int = int(os.getenv("REDIS_SESSION_TTL", "86400"))       # 24小时
    cache_ttl: int = int(os.getenv("REDIS_CACHE_TTL", "600"))             # 10分钟
    search_cache_ttl: int = int(os.getenv("REDIS_SEARCH_CACHE_TTL", "60")) # 1分钟

@dataclass
class EmbeddingConfig:
    """Embedding 模型配置"""
    model_name: str = "text-embedding-v4"
    dimension: int = 1024
    max_chars: int = 8000
    timeout: int = 30

@dataclass
class LLMConfig:
    """大模型配置"""
    chat_model: str = "qwen3-max"
    rewrite_model: str = "qwen3-1.8b"      # 查询改写使用小模型，速度快
    api_key: str = os.getenv("DASHSCOPE_API_KEY", os.getenv("QW_API_KEY", ""))
    rewrite_timeout: int = 8
    max_retries: int = 2

@dataclass
class TextSplitterConfig:
    """文本分割配置"""
    chunk_size: int = 1000
    chunk_overlap: int = 100
    separators: list = field(default_factory=lambda: [chr(10)+chr(10), chr(10), chr(32), '', chr(12290), chr(65307), chr(65292), chr(65281), chr(65311), chr(46), chr(33), chr(63), chr(59), chr(44)])

@dataclass
class HybridSearchConfig:
    """混合搜索配置"""
    vector_top_k: int = 30
    fulltext_top_k: int = 30
    rrf_constant_k: int = 60
    rewrite_variant_count: int = 2
    final_top_k: int = 10
    rerank_candidate_count: int = 20
    rerank_min_score: float = 0.1
    max_chunks_per_doc: int = 2
    hnsw_m: int = 24
    hnsw_ef_construction: int = 200
    hnsw_ef_search: int = 100

@dataclass
class RerankConfig:
    """Rerank 配置（使用通义千问 Rerank 模型）"""
    model: str = "qwen3-rerank"
    api_base: str = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank"
    api_key: str = os.getenv("DASHSCOPE_API_KEY", os.getenv("QW_API_KEY", ""))
    max_chars_per_doc: int = 4000
    timeout: int = 10

@dataclass
class ContextEnhanceConfig:
    """上下文增强配置"""
    enabled: bool = True
    batch_size: int = 10
    retry_delay: int = 5

@dataclass
class AppConfig:
    """全局配置入口"""
    postgresql: PostgreSQLConfig = field(default_factory=PostgreSQLConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    embedding: EmbeddingConfig = field(default_factory=EmbeddingConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    splitter: TextSplitterConfig = field(default_factory=TextSplitterConfig)
    search: HybridSearchConfig = field(default_factory=HybridSearchConfig)
    rerank: RerankConfig = field(default_factory=RerankConfig)
    enhance: ContextEnhanceConfig = field(default_factory=ContextEnhanceConfig)
    upload_dir: str = "./uploads"
    log_level: str = "INFO"
    page_title: str = "🎮 游戏百科智能问答系统"

config = AppConfig()
