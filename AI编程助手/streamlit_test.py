import streamlit as st
import time

st.set_page_config(
    page_title="Streamlit Test",
    page_icon="🧊",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config',
        'Report a bug': "https://docs.streamlit.io/develop/api-reference/configuration/st.set_page_config",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)


def main():
    # 标题
    st.title('Streamlit Test')
    st.header('Streamlit 一级标题')
    st.subheader('Streamlit 二级标题')
    # 段落文字
    st.write("我是一个专业的编程助手，能帮你解决代码问题、优化项目、提供技术方案，并解答计算机领域的各种疑问。")
    # 图片
    st.image("./resource/Screenshot_1.png")
    # 音频
    st.audio("./resource/周杰伦 - 那天下雨了.mp3")
    # 视频
    st.video("./resource/testvideo.mp4")
    # logo
    st.logo("./resource/logo.jpg")
    # 表格
    student_data = {
        '姓名': ['王林', '唐三', '萧炎'],
        '学号': ['002', '001', '003']
    }
    st.table(student_data)
    # 输入框
    input = st.text_input('请输入姓名', type='password')
    st.write(f'您输入的姓名为{input}')
    # 单选按钮
    sex = st.radio('请输入性别', ['男', '女'])
    st.write(sex)

    #-------------test st.empty()-----------------
    st.button("Start over")

    placeholder = st.empty()
    placeholder.markdown("Hello")
    time.sleep(1)

    placeholder.progress(0, "Wait for it...")
    time.sleep(1)
    placeholder.progress(50, "Wait for it...")
    time.sleep(1)
    placeholder.progress(100, "Wait for it...")
    time.sleep(1)

    with placeholder.container():
        st.line_chart({"data": [1, 5, 2, 6]})
        time.sleep(1)
        st.markdown("3...")
        time.sleep(1)
        st.markdown("2...")
        time.sleep(1)
        st.markdown("1...")
        time.sleep(1)

    placeholder.markdown("Poof!")
    time.sleep(1)

    placeholder.empty()


if __name__ == '__main__':
    main()
