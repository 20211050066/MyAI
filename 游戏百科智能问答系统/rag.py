from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda

from file_history_store import get_history
from vector_stores import VectorStoreService
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.prompts import ChatPromptTemplate, format_document, MessagesPlaceholder
import config_data as config
from langchain_community.chat_models import ChatTongyi


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


class RAGService(object):
    def __init__(self):
        self.vector_store_service = VectorStoreService(DashScopeEmbeddings(model=config.embedding_model_name))
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", config.system_prompt),
                ("system", "对话模式，请记住以下上下文"),
                MessagesPlaceholder(variable_name="history"),
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

        def get_retriever_args(input: dict) -> str:
            return input["input"]
        def get_prompt_template_args(input):
            output = {}
            output["input"] = input["input"]["input"]
            output["history"] = input["input"]["history"]
            output["context"] = input["context"]
            return output

            # 测试中间环节

        def test(input):
            print("=" * 20)
            print(input)
            print("=" * 20)
            return input

        chain = (
                {
                    "input": RunnablePassthrough(),
                    "context": RunnableLambda(get_retriever_args) | retriever | format_document
                } | RunnableLambda(get_prompt_template_args) | self.prompt_template | print_prompt | self.chat_model | StrOutputParser()
        )
        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history"
        )
        return conversation_chain


if __name__ == '__main__':
    res = RAGService().chain.invoke({"input": "这把我玩的洛克，有什么海克斯推荐吗"}, config.session_config)
    print(res)
