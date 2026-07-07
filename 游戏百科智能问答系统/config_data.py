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
similarity_threshold = 1
embedding_model_name = "text-embedding-v4"
chat_model_name = "qwen3-max"

# Prompt
system_prompt = "以我提供的已知参考资料为主，简洁和专业的回答用户问题。参考资料：{context}。"
user_prompt = "请回答问题：{input}"