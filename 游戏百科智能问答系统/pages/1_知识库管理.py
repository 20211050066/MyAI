"""知识库管理页面"""
import os
import tempfile
import streamlit as st

st.set_page_config(page_title="知识库管理", page_icon="📚", layout="wide")

from knowledge_base import KnowledgeBaseService
from doc_processor import SUPPORTED_TYPES
from db_pool import health_check as db_health

st.title("📚 知识库管理")

# 检查数据库状态
db_status = db_health()
if not db_status["postgresql"]:
    st.error("⚠️ PostgreSQL 未连接，请确保数据库已启动")
    st.stop()

if "kb_service" not in st.session_state:
    try:
        st.session_state.kb_service = KnowledgeBaseService()
    except Exception as e:
        st.error(f"知识库服务初始化失败：{e}")
        st.stop()

kb = st.session_state.kb_service

tab1, tab2, tab3 = st.tabs(["📤 上传文档", "📋 文档列表", "📊 统计信息"])

with tab1:
    st.subheader("上传文档到知识库")
    st.markdown(f"支持格式：{', '.join(SUPPORTED_TYPES.keys())}")
    uploaded_files = st.file_uploader(
        "选择文件",
        type=list(SUPPORTED_TYPES.keys()),
        accept_multiple_files=True,
    )
    if uploaded_files:
        for uf in uploaded_files:
            with st.spinner(f"正在处理：{uf.name}..."):
                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=os.path.splitext(uf.name)[1]
                ) as tmp:
                    tmp.write(uf.getvalue())
                    tmp_path = tmp.name
                try:
                    result = kb.upload_file(tmp_path, uf.name)
                    if result["success"]:
                        st.success(f"✅ **{uf.name}**：{result['message']}")
                    else:
                        st.info(f"ℹ️ **{uf.name}**：{result['message']}")
                except Exception as e:
                    st.error(f"❌ **{uf.name}**：处理失败 - {e}")
                finally:
                    os.unlink(tmp_path)

    st.divider()
    st.subheader("或直接输入文本")
    text_input = st.text_area("输入文本内容", height=150)
    text_filename = st.text_input("文档名称（可选）", placeholder="my_document.txt")
    if st.button("导入文本") and text_input.strip():
        name = text_filename.strip() or f"text_{hash(text_input) % 10000}.txt"
        result = kb.upload_text(text_input, name)
        if result["success"]:
            st.success(f"✅ {result['message']}")
        else:
            st.info(f"ℹ️ {result['message']}")

with tab2:
    st.subheader("文档列表")
    docs = kb.list_documents()
    if not docs:
        st.info("知识库为空，请先上传文档")
    else:
        for doc in docs:
            with st.expander(f"📄 {doc['filename']}（{doc['chunk_count']} 个片段）"):
                st.json(doc)
                if st.button("删除", key=f"del_{doc['id']}"):
                    kb.delete_document(doc["id"])
                    st.rerun()

with tab3:
    st.subheader("统计信息")
    stats = kb.get_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("文档数量", stats["document_count"])
    col2.metric("文本片段", stats["chunk_count"])
    col3.metric("总大小", f"{stats['total_size_mb']} MB")
