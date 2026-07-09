"""RAG 问答服务"""
import logging

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from config import config
from chat_history_store import get_history
from hybrid_search import HybridSearchService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "你是一个专业的游戏百科助手。请基于以下已知参考资料，简洁专业地回答用户问题。" \
                "如果参考资料不足以回答问题，请如实告知。\n\n参考资料：{context}"
USER_PROMPT = "问题：{input}"


class RAGService:
    """RAG 问答服务，支持流式输出"""

    def __init__(self):
        self.search_service = HybridSearchService()
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="history"),
            ("human", USER_PROMPT),
        ])
        self.chat_model = self._get_chat_model()
        self.chain = self._build_chain()

    def _get_chat_model(self):
        try:
            from langchain_community.chat_models import ChatTongyi
            return ChatTongyi(model=config.llm.chat_model)
        except ImportError:
            raise ImportError("请安装 langchain-community 和 dashscope")

    def _build_chain(self):
        def retrieve_context(inputs: dict) -> dict:
            raw = inputs.get("input", "")
            if isinstance(raw, dict):
                query = raw.get("input", "")
                history = raw.get("history", [])
            else:
                query = raw
                history = inputs.get("history", [])
            
            results = self.search_service.search(query)
            ctx = "\n\n".join(f"文档片段：{r['content']}\n来源 ID：{r['document_id']}" for r in results) if results else "无相关参考资料"
            return {"context": ctx, "input": query, "history": history}

        chain = RunnableLambda(retrieve_context) | self.prompt_template | self.chat_model | StrOutputParser()
        return RunnableWithMessageHistory(chain, get_history, input_messages_key="input", history_messages_key="history")

    def invoke(self, query: str, session_id: str = "default") -> str:
        """同步调用"""
        return self.chain.invoke({"input": query}, config={"configurable": {"session_id": session_id}})

    def stream(self, query: str, session_id: str = "default"):
        """流式调用"""
        return self.chain.stream({"input": query}, config={"configurable": {"session_id": session_id}})
