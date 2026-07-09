"""主页面 - 智能问答对话"""
import streamlit as st

st.set_page_config(page_title="游戏百科智能问答系统", page_icon="🎮", layout="wide")

from rag import RAGService
from db_pool import health_check

st.title("🎮 游戏百科智能问答系统")
st.caption("基于混合搜索的智能问答助手 | 支持文档上传、知识库管理、会话历史")

# 检查数据库连接状态
db_status = health_check()
if not db_status["postgresql"]:
    st.sidebar.warning("⚠️ PostgreSQL 未连接，部分功能不可用")
if not db_status["redis"]:
    st.sidebar.info("ℹ️ Redis 未连接，会话历史将使用本地存储")

if "message" not in st.session_state:
    st.session_state.message = [{"role": "assistant", "content": "你好！我是游戏百科助手，有什么可以帮你的吗？"}]

if "rag_service" not in st.session_state:
    try:
        st.session_state.rag_service = RAGService()
    except Exception as e:
        st.error(f"服务初始化失败：{e}")
        st.stop()

for msg in st.session_state.message:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("请输入你的问题...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.message.append({"role": "user", "content": prompt})

    cache_list = []
    with st.spinner("思考中..."):
        try:
            answer = st.session_state.rag_service.stream(prompt)
            st.chat_message("assistant").write_stream(
                (lambda a, c: (c.append(chunk) or chunk for chunk in a))(answer, cache_list)
            )
            st.session_state.message.append({"role": "assistant", "content": "".join(cache_list)})
        except Exception as e:
            st.error(f"查询失败：{e}")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 提示\n- 上传文档到知识库后可进行检索\n- 输入问题即可获得基于知识库的回答\n- 支持多轮对话")
