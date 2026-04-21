import streamlit as st
from Agent import AIAgent,APIAgent
from sessions import SessionManager

# 页面配置
st.set_page_config(
    page_title="AI编程助手",
    page_icon="👾",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': 'AI编程助手'
    }
)

st.title("AI编程助手")
st.logo("./resource/logo.png")


def initialize_session_state(agent: AIAgent, session_mgr: SessionManager):
    """
    初始化会话状态

    Args:
        agent: AIAgent实例
        session_mgr: SessionManager实例
    """
    if 'messages' not in st.session_state:
        st.session_state.messages = []

    if 'language' not in st.session_state:
        default_config = agent.get_default_config()
        st.session_state.language = default_config['language']

    if 'character' not in st.session_state:
        default_config = agent.get_default_config()
        st.session_state.character = default_config['character']

    if 'current_session_id' not in st.session_state:
        st.session_state.current_session_id = session_mgr.generate_current_session_id()


def render_sidebar(session_mgr: SessionManager):
    """
    渲染侧边栏配置

    Args:
        session_mgr: SessionManager实例

    Returns:
        更新后的语言和性格配置
    """
    with st.sidebar:
        st.subheader("基本信息")

        language = st.text_input(
            "使用语言",
            placeholder='请输入语言名称',
            value=st.session_state.language
        )

        if language:
            st.session_state.language = language

        character = st.text_area(
            "性格",
            placeholder='请输入语气与风格',
            height=300,
            value=st.session_state.character
        )

        if character:
            st.session_state.character = character

        st.divider()

        st.subheader("会话管理")

        if st.button("➕ 新建会话", use_container_width=True, width='stretch'):
            # 1.保存当前会话
            if st.session_state.current_session_id and len(st.session_state.messages) != 0:
                # 构建新的会话对象
                current_session = {
                    "session_id": st.session_state.current_session_id,
                    "language": st.session_state.language,
                    "character": st.session_state.character,
                    "messages": st.session_state.messages
                }
                saved_path = session_mgr.auto_save_session(current_session)
                print(f'文件保存成功：{saved_path}')
            elif st.session_state.current_session_id:
                print('当前id为空')
            elif len(st.session_state.messages) == 0:
                print('当前会话为空，请输入内容')

            # 2.新建会话
            new_session = session_mgr.create_session(
                language=st.session_state.language,
                character=st.session_state.character
            )
            st.session_state.current_session_id = new_session["session_id"]
            st.session_state.messages = []
            st.rerun()

        st.session_state.language = language
        st.session_state.character = character

        st.divider()

        st.subheader("历史会话")

        sessions = session_mgr.list_sessions()

        if sessions:
            for session_info in sessions:
                session_id = session_info["session_id"]
                session_title = session_info["title"]

                history_col1, history_col2 = st.columns([0.8, 0.2])
                with history_col1:
                    # 加载会话
                    if st.button(session_title, width='stretch', use_container_width=True, icon="📂",
                                 key=f'load_{session_id}',
                                 type="primary" if session_id == st.session_state.current_session_id else "secondary"):
                        session = session_mgr.load_session(session_id)
                        if session:
                            st.session_state.messages = session["messages"]
                            st.session_state.current_session_id = session_id
                            st.session_state.language = session["language"]
                            st.session_state.character = session["character"]
                            st.rerun()
                        else:
                            st.error("会话加载失败")
                with history_col2:
                    # 删除会话
                    if st.button("🗑️", width='stretch', use_container_width=True, key=f'delete_{session_id}'):
                        if session_mgr.delete_session(session_id):
                            # 如果当前会话被删除，则重新加载
                            if st.session_state.current_session_id == session_id:
                                st.session_state.messages = []
                                st.session_state.current_session_id = session_mgr.generate_current_session_id()
                            st.rerun()
                        else:
                            st.error("会话删除失败")


    return st.session_state.language, st.session_state.character


def display_chat_history():
    """显示历史会话记录"""
    st.text(f'会话名称：{st.session_state.current_session_id}')
    for message in st.session_state.messages:
        st.chat_message(message["role"]).write(message["content"])


def handle_user_input(agent: AIAgent, session_mgr: SessionManager):
    """
    处理用户输入并调用AI助手

    Args:
        agent: AIAgent实例
        session_mgr: SessionManager实例
    """
    message = st.chat_input("给助手发送消息")

    if message:
        # 显示用户消息
        st.chat_message("user").write(message)
        print("调用AI大模型，输入提示词:", message)

        # 保存用户消息到会话历史
        st.session_state.messages.append({"role": "user", "content": message})

        # 构建系统提示词
        system_prompt = agent.build_system_prompt(
            st.session_state.language,
            st.session_state.character
        )

        # 调用AI模型（流式响应）
        response = agent.chat(
            messages=st.session_state.messages,
            system_prompt=system_prompt,
            stream=True
        )

        # 流式显示AI响应
        response_message = st.empty()
        full_response = ""

        for full_response in agent.get_stream_response(response):
            response_message.chat_message("assistant").write(full_response)

        print("模型返回结果为:", full_response)

        # 保存AI响应到会话历史
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_response
        })
        session_mgr.auto_save_session({
            "session_id": st.session_state.current_session_id,
            "language": st.session_state.language,
            "character": st.session_state.character,
            "messages": st.session_state.messages
        })


def main():
    """主函数"""
    # 创建AI助手实例
    agent = AIAgent()

    # 创建APIAgent实例（专门用于生成会话标题）
    title_agent = APIAgent()

    # 创建会话管理器，传入title_agent用于生成标题
    session_mgr = SessionManager(agent=title_agent)

    # 初始化会话状态
    initialize_session_state(agent, session_mgr)

    # 显示聊天历史
    display_chat_history()

    # 处理用户输入
    handle_user_input(agent, session_mgr)

    # 渲染侧边栏
    render_sidebar(session_mgr)


if __name__ == '__main__':
    main()
