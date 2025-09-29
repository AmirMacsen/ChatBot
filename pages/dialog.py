
import streamlit as st
import uuid

from streamlit_chatbox import ChatBox

from configs.model import TEMPERATURE, HISTORY_LEN
from configs.prompt import PROMPT_TEMPLATES
from pages.api_utils import ApiRequest

chat_box = ChatBox()

def dialogue_page(api: ApiRequest, is_lite: bool = False):
    st.session_state.setdefault("conversation_ids", {})
    st.session_state["conversation_ids"].setdefault(chat_box.cur_chat_name, uuid.uuid4().hex)
    st.session_state.setdefault("file_chat_id", None)

    running_models = api.list_running_models()
    print(running_models)
    if not running_models:
        st.toast("当前没有运行中的模型，请先启动模型。")
        return

    default_model = list(running_models.keys())[0]
    if not chat_box.chat_inited:
        st.toast(
            "欢迎使用ChatBot\n\n"
            f"当前运行模型: {default_model}"
        )
        chat_box.init_session()

    with st.sidebar:
        # 多会话
        conv_names = list(st.session_state["conversation_ids"].keys())
        index = 0
        if st.session_state.get("cur_conv_name") in conv_names:
            index = conv_names.index(st.session_state.get("cur_conv_name"))
        conversation_name = st.selectbox("当前会话：", conv_names, index=index)
        chat_box.use_chat_name(conversation_name)
        conversation_id = st.session_state["conversation_ids"][conversation_name]
        def on_mode_change():
            mode = st.session_state.dialogue_mode
            text = f"已切换到 {mode} 模式。"
            if mode == "知识库问答":
                cur_kb = st.session_state.get("selected_kb")
                if cur_kb:
                    text = f"{text} 当前知识库： `{cur_kb}`。"
            st.toast(text)

        # 选择对话模式
        dialogue_modes = ["LLM 对话",
                          "知识库问答",
                          "文件对话",
                          "搜索引擎问答",
                          "自定义Agent问答",
                          ]
        dialogue_mode = st.selectbox("请选择对话模式：",
                                     dialogue_modes,
                                     index=0,
                                     on_change=on_mode_change,
                                     key="dialogue_mode",
                                     )
        if not running_models:
            st.toast("当前没有运行中的模型，请先启动模型。")
            return

        llm_models = list(running_models.keys())
        # 选择llm模型
        llm_model = st.selectbox("选择LLM模型：",
                                 llm_models,
                                 index,
                                 key="llm_model",
                                 )

        index_prompt = {
            "LLM 对话": "llm_chat",
            "自定义Agent问答": "agent_chat",
            "搜索引擎问答": "search_engine_chat",
            "知识库问答": "knowledge_base_chat",
            "文件对话": "knowledge_base_chat",
        }
        prompt_templates_kb_list = list(PROMPT_TEMPLATES[index_prompt[dialogue_mode]].keys())
        prompt_template_name = prompt_templates_kb_list[0]
        if "prompt_template_select" not in st.session_state:
            st.session_state.prompt_template_select = prompt_templates_kb_list[0]

        def prompt_change():
            text = f"已切换为 {prompt_template_name} 模板。"
            st.toast(text)

        prompt_template_select = st.selectbox(
            "请选择Prompt模板：",
            prompt_templates_kb_list,
            index=0,
            on_change=prompt_change,
            key="prompt_template_select",
        )
        prompt_template_name = st.session_state.prompt_template_select
        temperature = st.slider("Temperature：", 0.0, 2.0, TEMPERATURE, 0.05)
        history_len = st.number_input("历史对话轮数：", 0, 20, HISTORY_LEN)

    chat_box.output_messages()
    chat_input_placeholder = "请输入对话内容，换行请使用Shift+Enter。输入/help查看自定义命令 "
    prompt = st.chat_input(chat_input_placeholder, key="prompt")
    if dialogue_mode == "LLM 对话":
        chat_box.ai_say("正在思考...")
        text = ""
        message_id = ""
        r = api.chat_chat(prompt,
                          history=[],
                          conversation_id=conversation_id,
                          model=llm_model,
                          prompt_name=prompt_template_name,
                          temperature=temperature)
        for t in r:
            text += t.get("text", "")
            chat_box.update_msg(text)
            message_id = t.get("message_id", "")

        metadata = {
            "message_id": message_id,
        }
        chat_box.update_msg(text, streaming=False, metadata=metadata)  # 更新最终的字符串，去除光标




