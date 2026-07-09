import streamlit as st
from rag import RAGService

# 标题
st.title("游戏百科助手")
st.divider()

if "message" not in st.session_state:
    st.session_state.message = [{}]
for message in st.session_state.message:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("assistant").write(message["content"])
# 输入框
prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.message.append({"role": "user", "content": prompt})
    rag_service = RAGService()
    with st.spinner("思考中..."):
        # 获取答案
        answer = rag_service.chain.invoke({"input": {"input": prompt, "history": []}})
        # 输出答案
        st.chat_message("assistant:").write(answer)
        st.session_state.message.append({"role": "assistant", "content": answer})