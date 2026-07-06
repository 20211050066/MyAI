import time

import streamlit as st
from knowledge_base import KnowledgeBaseService

st.title("知识库更新服务")
st.logo("resource/onefish.png")

# 文件上传框
upload_file = st.file_uploader(
    "上传TXT文件",
    type=["txt"],
    accept_multiple_files=False,
    key="file_uploader",
)

if "kb_service" not in st.session_state:
    st.session_state.kb_service = KnowledgeBaseService()

# 处理文件上传
if upload_file:
    # 提取文件信息
    file_name = upload_file.name
    file_type = upload_file.type
    file_size = upload_file.size / 1024

    st.subheader(f"文件名：{file_name}")
    st.write(f'格式:{file_type} | 大小:{file_size:.2f}KB')

    # 获取文件内容
    file_content = upload_file.getvalue().decode("utf-8")

    # spinner内的代码执行中，会有一个loading动画
    with st.spinner("载入知识库中..."):
        time.sleep(1)
        result = st.session_state.kb_service.upload_by_str(file_content, file_name)
        st.write(result)


