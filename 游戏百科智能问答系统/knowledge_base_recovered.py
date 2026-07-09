"""知识库管理服�?""
import hashlib
import logging
import os
from typing import List

from config import config
from db_pool import get_pg_conn
from doc_processor import extract_text
from embeddings import EmbeddingService
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


def get_string_md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


class KnowledgeBaseService:
    """知识库管理服务，支持上传/索引/查询/删除"""

    def __init__(self):
        self.embedding_service = EmbeddingService()
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.splitter.chunk_size,
            chunk_overlap=config.splitter.chunk_overlap,
            separators=config.splitter.separators,
            length_function=len,
        )

    def upload_file(self, filepath: str, filename: str, operator: str = "system") -> dict:
        """上传文件到知识库"""
        content = extract_text(filepath)
        if not content.strip():
            return {"success": False, "message": "文件内容为空，无法处�?}
        return self._index_content(content, filename, os.path.splitext(filename)[1].lower(),
                                   os.path.getsize(filepath), operator)

    def upload_text(self, text: str, filename: str, operator: str = "system") -> dict:
        """直接上传文本到知识库"""
        return self._index_content(text, filename, ".txt", len(text), operator)

    def _index_content(self, content, filename, file_type, file_size, operator):
        """索引内容到知识库（含 MD5 去重、分块��Embedding、入库）"""
        md5 = get_string_md5(content)
        if self._check_exists(md5):
            return {"success": False, "message": f"文件已存在（MD5: {md5[:8]}...），跳过处理"}

        chunks = self.splitter.split_text(content) if len(content) > config.splitter.chunk_size else [content]
        logger.info("正在生成 %d 个片段的 Embedding...", len(chunks))
        embeddings = self.embedding_service.embed_documents(chunks)

        try:
            doc_id = self._insert_document(filename, file_type, file_size, md5, len(chunks), operator)
            self._insert_chunks(doc_id, chunks, embeddings)
            logger.info("知识库索引完�? %s�?d 片段�?, filename, len(chunks))
            return {"success": True, "message": f"成功导入 {len(chunks)} 个文本片�?,
                    "chunk_count": len(chunks), "document_id": doc_id}
        except Exception as e:
            logger.error("知识库索引失�? %s", e, exc_info=True)
            return {"success": False, "message": f"索引失败: {str(e)}"}

    def _check_exists(self, md5):
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM documents WHERE md5 = %s", (md5,))
                return cur.fetchone() is not None

    def _insert_document(self, filename, file_type, file_size, md5, chunk_count, operator):
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO documents (filename, file_type, file_size, md5, chunk_count, operator) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                            (filename, file_type, file_size, md5, chunk_count, operator))
                return cur.fetchone()[0]

    def _insert_chunks(self, doc_id, chunks, embeddings):
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                for idx, (chunk, emb) in enumerate(zip(chunks, embeddings)):
                    emb_str = "{" + ",".join(str(v) for v in emb) + "}"
                    cur.execute("INSERT INTO document_chunks (document_id, chunk_index, content, embedding) VALUES (%s,%s,%s,%s::double precision[])",
                                (doc_id, idx, chunk, emb_str))

    def list_documents(self) -> List[dict]:
        """列出扢�有文�?""
        try:
            with get_pg_conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT id, filename, file_type, file_size, chunk_count, upload_time, operator FROM documents ORDER BY upload_time DESC")
                    return [{"id": r[0], "filename": r[1], "file_type": r[2], "file_size": r[3],
                             "chunk_count": r[4], "upload_time": r[5].strftime("%Y-%m-%d %H:%M:%S") if r[5] else "",
                             "operator": r[6]} for r in cur.fetchall()]
        except Exception as e:
            logger.warning("查询文档列表失败: %s", e)
            return []

    def delete_document(self, doc_id: int) -> bool:
        """删除文档及其扢�有片�?""
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM documents WHERE id = %s", (doc_id,))
                return cur.rowcount > 0

    def get_document_chunks(self, doc_id: int) -> List[dict]:
        """获取文档的所有片�?""
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, chunk_index, content, created_at FROM document_chunks WHERE document_id = %s ORDER BY chunk_index", (doc_id,))
                return [{"id": r[0], "index": r[1],
                         "content": (r[2][:200] + "...") if len(r[2]) > 200 else r[2],
                         "created_at": r[3].strftime("%Y-%m-%d %H:%M:%S") if r[3] else ""} for r in cur.fetchall()]

    def get_stats(self) -> dict:
        """知识库统计信�?""
        with get_pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM documents")
                doc_count = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM document_chunks")
                chunk_count = cur.fetchone()[0]
                cur.execute("SELECT COALESCE(SUM(file_size), 0) FROM documents")
                total_size = cur.fetchone()[0]
                return {"document_count": doc_count, "chunk_count": chunk_count,
                        "total_size_bytes": total_size, "total_size_mb": round(total_size / 1024 / 1024, 2)}
