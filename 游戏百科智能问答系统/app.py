"""主页面 - 智能问答对话"""
import uuid
from datetime import datetime

import streamlit as st

st.set_page_config(page_title="游戏百科智能问答系统", page_icon="🎮", layout="wide")

from rag import RAGService
from db_pool import health_check
from chat_history_store import RedisChatHistoryStore
from langchain_core.messages import HumanMessage, AIMessage

WELCOME_MESSAGE = {
    "role": "assistant",
    "content": "你好！我是游戏百科助手，有什么可以帮你的吗？",
}


def new_session_id() -> str:
    """生成新的会话 ID"""
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"session_{now}_{uuid.uuid4().hex[:8]}"


def list_sessions() -> list:
    """列出所有已持久化的会话 ID"""
    return RedisChatHistoryStore.list_sessions()


def delete_session(session_id: str) -> None:
    """删除指定会话的 Redis 历史记录"""
    RedisChatHistoryStore(session_id).clear()


def read_session_messages(session_id: str) -> list:
    """读取 Redis 历史消息并转换成页面消息格式"""
    messages = []
    for msg in RedisChatHistoryStore(session_id).messages:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})
    return messages


def ensure_session_state_for_session(session_id: str) -> None:
    """把页面状态切换到一个新建会话"""
    st.session_state.current_session_id = session_id
    st.session_state["in_new_session"] = True
    st.session_state.message = [WELCOME_MESSAGE]


def load_session(session_id: str) -> None:
    """切换到指定历史会话并加载其消息"""
    st.session_state.current_session_id = session_id
    st.session_state["in_new_session"] = False
    st.session_state.message = read_session_messages(session_id) or [WELCOME_MESSAGE]


st.title("🎮 游戏百科智能问答系统")
st.caption("基于混合搜索的智能问答助手 | 支持文档上传、知识库管理、会话历史")

# 检查数据库连接状态
db_status = health_check()
if not db_status["postgresql"]:
    st.sidebar.warning("⚠️ PostgreSQL 未连接，部分功能不可用")
if not db_status["redis"]:
    st.sidebar.info("ℹ️ Redis 未连接，会话历史暂不可用")

if "rag_service" not in st.session_state:
    try:
        st.session_state.rag_service = RAGService()
    except Exception as e:
        st.error(f"服务初始化失败：{e}")
        st.stop()

# ---------- 侧边栏会话管理 ----------
st.sidebar.header("会话管理")

existing_sessions = list_sessions()

# 当前会话 ID
if "current_session_id" not in st.session_state:
    # 仅在首次加载时设置默认会话 ID，之后完全由用户在侧边栏中选择
    if existing_sessions:
        st.session_state.current_session_id = existing_sessions[0]
        st.session_state["in_new_session"] = False
    else:
        st.session_state.current_session_id = new_session_id()
        st.session_state["in_new_session"] = True

if "message" not in st.session_state:
    if st.session_state.current_session_id in existing_sessions:
        st.session_state.message = (
            read_session_messages(st.session_state.current_session_id) or [WELCOME_MESSAGE]
        )
    else:
        st.session_state.message = [WELCOME_MESSAGE]

# 新建会话按钮
if st.sidebar.button("➕ 新建会话", use_container_width=True):
    new_id = new_session_id()
    ensure_session_state_for_session(new_id)
    st.rerun()

# 会话选择列表：仅展示已有持久化记录的会话
# 新建会话在产生聊天记录（被持久化）之前，不会出现在列表中
display_sessions = existing_sessions.copy()

in_new_session = (
    st.session_state.get("in_new_session", False)
    and st.session_state.current_session_id not in display_sessions
)

if display_sessions:
    st.sidebar.markdown("#### 历史会话")
    for sid in display_sessions:
        is_active = (not in_new_session) and (
            sid == st.session_state.current_session_id
        )
        clicked = st.sidebar.button(
            f"🗂 {sid}",
            key=f"session_btn_{sid}",
            use_container_width=True,
            type="primary" if is_active else "secondary",
        )
        if clicked and not is_active:
            load_session(sid)
            st.rerun()

st.sidebar.caption(f"当前会话 ID：`{st.session_state.current_session_id}`")

# 删除当前会话
if st.sidebar.button("🗑 删除当前会话", use_container_width=True):
    to_delete = st.session_state.current_session_id
    delete_session(to_delete)
    # 删除后自动切换到其他会话或新建一个
    remaining = list_sessions()
    if remaining:
        load_session(remaining[0])
    else:
        ensure_session_state_for_session(new_session_id())
    if hasattr(st, "toast"):
        st.toast(f"已删除会话：{to_delete}", icon="🗑")
    st.rerun()

# ---------- 主聊天区 ----------
for msg in st.session_state.message:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("请输入你的问题...")

if prompt:
    session_id = st.session_state.current_session_id
    st.chat_message("user").write(prompt)
    st.session_state.message.append({"role": "user", "content": prompt})

    cache_list = []
    with st.spinner("思考中..."):
        try:
            answer = st.session_state.rag_service.stream(
                prompt, session_id=session_id
            )
            st.chat_message("assistant").write_stream(
                (lambda a, c: (c.append(chunk) or chunk for chunk in a))(answer, cache_list)
            )
            st.session_state.message.append({"role": "assistant", "content": "".join(cache_list)})
            st.session_state["in_new_session"] = False
        except Exception as e:
            st.error(f"查询失败：{e}")

# st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 提示\n- 上传文档到知识库后可进行检索\n- 输入问题即可获得基于知识库的回答\n- 支持多轮对话")
