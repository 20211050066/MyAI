from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.prompts import ChatPromptTemplate, format_document
import config_data as config
from langchain_community.chat_models import ChatTongyi

def print_prompt(prompt):
    print("="*20)
    print(prompt.to_string())
    print("="*20)
    return  prompt

class RAGService(object):
    def __init__(self):
        self.vector_store_service = VectorStoreService(DashScopeEmbeddings(model=config.embedding_model_name))
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", config.system_prompt),
                ("human", config.user_prompt),
            ]
        )
        self.chat_model = ChatTongyi(model=config.chat_model_name)
        self.chain = self.__get_chain()

    def __get_chain(self):
        retriever = self.vector_store_service.get_retriever()

        def format_document(docs):
            if not docs:
                return "无相关参考资料"
            formatted_str = ""
            for doc in docs:
                formatted_str += f"文档片段：{doc.page_content}\n文档元数据：{doc.metadata}\n\n"
            return formatted_str

        chain = (
                {
                    "input":RunnablePassthrough(),
                    "context": retriever | format_document
                } | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )
        return chain


if __name__ == '__main__':
    res = RAGService().chain.invoke("这把我玩的洛克，有什么海克斯推荐吗")
    print(res)