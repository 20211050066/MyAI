"""对话历史管理页面"""
import streamlit as st

st.set_page_config(page_title="对话历史", page_icon="💬", layout="wide")

from chat_history_store import RedisChatHistoryStore
from langchain_core.messages import HumanMessage, AIMessage

st.title("💬 对话历史")

sessions = RedisChatHistoryStore.list_sessions()

if not sessions:
    st.info("暂无会话历史")
else:
    selected = st.selectbox("选择会话", sessions)
    if selected:
        store = RedisChatHistoryStore(selected)
        msgs = store.messages
        if not msgs:
            st.info("该会话暂无消息")
        else:
            st.caption(f"共 {len(msgs)} 条消息")
            for msg in msgs:
                if isinstance(msg, HumanMessage):
                    st.chat_message("user").write(msg.content)
                elif isinstance(msg, AIMessage):
                    st.chat_message("assistant").write(msg.content)

            col1, col2, col3 = st.columns([1, 1, 4])
            with col1:
                if st.button("🗑️ 清空", type="primary"):
                    store.clear()
                    st.rerun()
            with col2:
                if st.button("🔄 刷新"):
                    st.rerun()
