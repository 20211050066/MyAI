"""数据库连接池管理"""
import logging
from contextlib import contextmanager
from typing import Optional, Generator

from config import config

logger = logging.getLogger(__name__)

_pg_pool = None
_redis_client = None


def _get_pg_pool():
    global _pg_pool
    if _pg_pool is None:
        try:
            import psycopg2
            from psycopg2 import pool
            _pg_pool = pool.ThreadedConnectionPool(
                config.postgresql.min_conn,
                config.postgresql.max_conn,
                dsn=config.postgresql.dsn,
            )
        except Exception as e:
            logger.error("PostgreSQL 连接失败: %s", e)
            raise ConnectionError(
                "PostgreSQL 无法连接，请确认数据库已启动。"
                "配置: host=%s port=%s dbname=%s" % (
                    config.postgresql.host, config.postgresql.port, config.postgresql.dbname
                )
            ) from e
    return _pg_pool


@contextmanager
def get_pg_conn() -> Generator:
    """获取 PostgreSQL 连接（上下文管理器，自动提交/回滚）"""
    pool = _get_pg_pool()
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def ensure_pgvector():
    """确保 pgvector 扩展安装并创建基础表结构"""
    with get_pg_conn() as conn:
        with conn.cursor() as cur:
            # pgvector 扩展未安装，使用 double precision[] 数组存储向量
            cur.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id SERIAL PRIMARY KEY,
                    filename VARCHAR(500) NOT NULL,
                    file_type VARCHAR(100),
                    file_size BIGINT DEFAULT 0,
                    md5 VARCHAR(32) UNIQUE,
                    chunk_count INTEGER DEFAULT 0,
                    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    operator VARCHAR(100) DEFAULT 'system'
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS document_chunks (
                    id SERIAL PRIMARY KEY,
                    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                    chunk_index INTEGER DEFAULT 0,
                    content TEXT NOT NULL,
                    embedding double precision[],
                    context TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            _create_index(cur, "idx_chunks_document_id",
                "CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id)")
            _create_index(cur, "idx_chunks_content_tsv",
                "CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON document_chunks USING GIN (to_tsvector('simple', COALESCE(content, '')))")
    logger.info("数据库表结构已就绪")


def _create_index(cur, name, sql, params=None, hnsw=False):
    """创建索引，HNSW 索引可延迟创建"""
    cur.execute("SELECT 1 FROM pg_indexes WHERE indexname = %s", (name,))
    if cur.fetchone():
        return
    try:
        if params:
            cur.execute(sql, params)
        else:
            cur.execute(sql)
        logger.info("索引创建成功: %s", name)
    except Exception as e:
        if hnsw:
            logger.warning("HNSW 索引延迟创建（需要先插入数据）: %s", e)
        else:
            raise


def get_redis():
    """获取 Redis 客户端（懒加载单例）"""
    global _redis_client
    if _redis_client is None:
        import redis as redis_lib
        _redis_client = redis_lib.Redis(
            host=config.redis.host,
            port=config.redis.port,
            db=config.redis.db,
            password=config.redis.password,
            decode_responses=config.redis.decode_responses,
            protocol=2,
        )
        _redis_client.ping()
    return _redis_client


def health_check() -> dict:
    """检查各服务健康状态"""
    status = {"postgresql": False, "redis": False, "pgvector": False}
    try:
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.execute("SELECT 1 WHERE EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='document_chunks' AND column_name='embedding')")
                status["pgvector"] = cur.fetchone() is not None
        status["postgresql"] = True
    except Exception:
        pass
    try:
        r = get_redis()
        if r:
            r.ping()
            status["redis"] = True
    except Exception:
        pass
    return status
