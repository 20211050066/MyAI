"""RAG 问答服务"""
import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda

from config import config
from chat_history_store import RedisChatHistoryStore
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
            query = inputs.get("input", "")
            history = inputs.get("history", [])

            results = self.search_service.search(query)
            ctx = (
                "\n\n".join(
                    f"文档片段：{r['content']}\n来源 ID：{r['document_id']}"
                    for r in results
                )
                if results
                else "无相关参考资料"
            )
            return {"context": ctx, "input": query, "history": history}

        return RunnableLambda(retrieve_context) | self.prompt_template | self.chat_model | StrOutputParser()

    def _load_history(self, session_id: str):
        """读取会话之前的消息"""
        return RedisChatHistoryStore(session_id).messages

    def _save_turn(self, session_id: str, query: str, answer: str) -> None:
        """把当前一轮问答写入 Redis 会话历史"""
        RedisChatHistoryStore(session_id).add_messages([
            HumanMessage(content=query),
            AIMessage(content=answer),
        ])

    def invoke(self, query: str, session_id: str = "default") -> str:
        """同步调用"""
        history = self._load_history(session_id)
        answer = self.chain.invoke({"input": query, "history": history})
        self._save_turn(session_id, query, answer)
        return answer

    def stream(self, query: str, session_id: str = "default"):
        """流式调用"""
        return self._stream(query, session_id)

    def _stream(self, query: str, session_id: str):
        history = self._load_history(session_id)
        chunks = []
        for chunk in self.chain.stream({"input": query, "history": history}):
            chunks.append(chunk)
            yield chunk
        if chunks:
            self._save_turn(session_id, query, "".join(chunks))
