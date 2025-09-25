import os

import streamlit as st
from streamlit_option_menu import option_menu

"""
创建一个webui界面
"""
st.set_page_config(
        "ChatBot WebUI",
        os.path.join("img", "chatchat_icon_blue_square_v2.png"),
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/chatchat-space/Langchain-Chatchat',
            'Report a bug': "https://github.com/chatchat-space/Langchain-Chatchat/issues",
            'About': f"""欢迎使用 Langchain-Chatchat WebUI！"""
        }
)

pages = {
    "对话": {
        "icon": "chat",
        "func": "",
    },
    "知识库管理": {
        "icon": "hdd-stack",
        "func": "knowledge_base_page",
    },
}

with st.sidebar:
    st.image(
        os.path.join(
            "img",
            "logo-long-chatchat-trans-v2.png"
        ),
        use_column_width=True
    )
    st.caption(
        unsafe_allow_html=True,
    )
    options = list(pages)
    icons = [x["icon"] for x in pages.values()]

    default_index = 0
    selected_page = option_menu(
        "",
        options=options,
        icons=icons,
        # menu_icon="chat-quote",
        default_index=default_index,
    )

    if selected_page in pages:
        pages[selected_page]["func"](api=api, is_lite=is_lite)