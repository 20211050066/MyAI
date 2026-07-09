-- PostgreSQL ?????
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(500) NOT NULL,
    file_type VARCHAR(100),
    file_size BIGINT DEFAULT 0,
    md5 VARCHAR(32) UNIQUE,
    chunk_count INTEGER DEFAULT 0,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    operator VARCHAR(100) DEFAULT "system"
);

CREATE TABLE IF NOT EXISTS document_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INTEGER DEFAULT 0,
    content TEXT NOT NULL,
    embedding vector(1024),
    context TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_chunks_content_tsv ON document_chunks USING GIN (to_tsvector("simple", COALESCE(content, "")));
-- HNSW ??
CREATE INDEX IF NOT EXISTS idx_chunks_embedding_hnsw ON document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 24, ef_construction = 200);
