md5_path = "./md5.text"

# Chromadb
collection_name = "game_wiki"
persist_directory = "./chroma_db"

# Spliter
chunk_size = 1000
chunk_overlap = 100
separators = ['\n\n', '\n', ' ', '', '。', '！', '？', '；', '，', ',', '!', '?', '.',';']
max_split_chunk_number = 1000

# RAG
similarity_threshold = 2