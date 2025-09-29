import streamlit as st
import uuid
from streamlit_chatbox import ChatBox
from configs.model import TEMPERATURE, HISTORY_LEN
from configs.prompt import PROMPT_TEMPLATES
from pages.api_utils import ApiRequest
from pages.components import render_conversation_management, render_model_config, render_mode_specific_config

chat_box = ChatBox()


def dialogue_page(api: ApiRequest, is_lite: bool = False):
    # 初始化会话状态
    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(chat_box.cur_chat_name, uuid.uuid4().hex)
    st.session_state.setdefault("file_chat_id", None)

    # 检查运行中模型
    running_models = api.list_running_models()
    if not running_models:
        st.toast("⚠️ 当前没有运行中的模型，请先启动模型。")
        return
    default_model = list(running_models.keys())[0]

    # 初始化提示
    if not chat_box.chat_inited:
        st.toast(f"👋 欢迎使用ChatBot\n当前运行模型: {default_model}")
        chat_box.init_session()

    # 页面布局：左侧侧边栏（配置），右侧主内容（聊天）
    col_sidebar, col_main = st.columns(
        [1, 4],  # 侧边栏:主内容 = 1:4，扩大主内容区
        gap="large"  # 增加列之间的间隙
    )

    with col_sidebar:
        # 对话模式选择（核心差异化入口）
        dialogue_modes = ["LLM 对话", "知识库问答", "文件对话", "搜索引擎问答", "自定义Agent问答"]
        dialogue_mode = st.selectbox(
            "对话模式",
            dialogue_modes,
            index=0,
            key="dialogue_mode",
            format_func=lambda x: f"📌 {x}"  # 加图标区分
        )

        # 渲染公共组件
        conversation_id = render_conversation_management(chat_box, st.session_state["conversation_ids"])
        llm_model, prompt_template, temperature, history_len = render_model_config(
            running_models=list(running_models.keys()),
            dialogue_mode=dialogue_mode,
            prompt_templates=PROMPT_TEMPLATES
        )

        # 渲染模式专属配置
        mode_config = render_mode_specific_config(dialogue_mode, api)

    with col_main:
        # 主标题（带模式标识）
        mode_icons = {
            "LLM 对话": "💬",
            "知识库问答": "📚",
            "文件对话": "📂",
            "搜索引擎问答": "🔍",
            "自定义Agent问答": "🤖"
        }
        st.header(f"{mode_icons[dialogue_mode]} {dialogue_mode}", divider="blue")

        # 聊天区域
        chat_box.output_messages()

        # 输入区域（根据模式调整提示）
        placeholders = {
            "LLM 对话": "请输入对话内容...",
            "知识库问答": "请输入关于知识库的问题...",
            "文件对话": "请输入关于上传文件的问题...",
            "搜索引擎问答": "请输入需要搜索的问题...",
            "自定义Agent问答": "请输入需要Agent处理的问题..."
        }
        prompt = st.chat_input(placeholders[dialogue_mode], key="prompt")

        if prompt:
            # 显示加载状态
            with st.spinner("思考中..."):
                # 根据模式调用不同API
                if dialogue_mode == "LLM 对话":
                    chat_box.ai_say("正在生成回答...")
                    text = ""
                    message_id = ""
                    # 流式获取结果
                    r = api.chat_chat(
                        prompt,
                        history=[],
                        conversation_id=conversation_id,
                        model=llm_model,
                        prompt_name=prompt_template,
                        temperature=temperature
                    )
                    for t in r:
                        text += t.get("text", "")
                        chat_box.update_msg(text)
                        message_id = t.get("message_id", "")
                    # 更新最终结果
                    chat_box.update_msg(text, streaming=False, metadata={"message_id": message_id})