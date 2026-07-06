from langchain_chroma import Chroma
from langchain_community.embeddings import DashScopeEmbeddings

import config_data as config


class VectorStoreService(object):
    def __init__(self,embedding_model: DashScopeEmbeddings):
        self.embedding_model = embedding_model
        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=config.persist_directory,
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(serch_kwargs={"k": config.similarity_threshold})