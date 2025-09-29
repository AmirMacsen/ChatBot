import streamlit as st
import uuid
from typing import List, Dict, Callable


def render_conversation_management(chat_box, conversation_ids: Dict):
    """渲染会话管理组件（公共）"""
    conv_names = list(conversation_ids.keys())
    index = conv_names.index(st.session_state.get("cur_conv_name")) if st.session_state.get(
        "cur_conv_name") in conv_names else 0
    with st.container(border=True, padding=1):
        st.subheader("会话管理", divider="gray")
        col1, col2 = st.columns([3, 1])
        with col1:
            conversation_name = st.selectbox(
                "当前会话：",
                conv_names,
                index=index,
                label_visibility="collapsed"
            )
        with col2:
            if st.button("+ 新建会话", use_container_width=True):
                new_name = f"会话{len(conv_names) + 1}"
                conversation_ids[new_name] = uuid.uuid4().hex
                st.session_state["cur_conv_name"] = new_name
                st.rerun()

        chat_box.use_chat_name(conversation_name)
        conversation_id = conversation_ids[conversation_name]

        # 会话操作按钮（悬浮显示）
        with st.expander("会话操作", expanded=False):
            col_del, col_clear = st.columns(2)
            with col_del:
                if st.button("删除当前会话", use_container_width=True, type="secondary"):
                    if len(conv_names) > 1:
                        conversation_ids.pop(conversation_name)
                        chat_box.del_chat_name(conversation_name)
                        st.session_state["cur_conv_name"] = conv_names[0] if conv_names else ""
                        st.rerun()
                    else:
                        st.error("至少保留一个会话")
            with col_clear:
                if st.button("清空当前会话", use_container_width=True, type="secondary"):
                    chat_box.reset_history()
                    st.success("已清空")
        return conversation_id


def render_model_config(
        running_models: List[str],
        dialogue_mode: str,
        prompt_templates: Dict,
        on_model_change: Callable = None,
        on_prompt_change: Callable = None
):
    """渲染模型和Prompt配置组件（公共）"""
    with st.container(border=True, padding=1):
        st.subheader("模型配置", divider="gray")

        # 模型选择（带运行状态标识）
        llm_model = st.selectbox(
            "LLM模型：",
            running_models,
            index=0,
            format_func=lambda x: f"{x} 🟢" if x in running_models else x,
            on_change=on_model_change
        )

        # 根据对话模式筛选Prompt模板
        prompt_type = {
            "LLM 对话": "llm_chat",
            "知识库问答": "knowledge_base_chat",
            "文件对话": "knowledge_base_chat",
            "搜索引擎问答": "search_engine_chat",
            "自定义Agent问答": "agent_chat",
        }[dialogue_mode]
        prompt_templates_kb_list = list(prompt_templates[prompt_type].keys())

        # Prompt模板选择
        prompt_template = st.selectbox(
            "Prompt模板：",
            prompt_templates_kb_list,
            index=0,
            on_change=on_prompt_change
        )

        # 生成参数（折叠显示）
        with st.expander("高级参数", expanded=False):
            col_temp, col_history = st.columns(2)
            with col_temp:
                temperature = st.slider("温度（创造性）", 0.0, 2.0, 0.7, 0.05)
            with col_history:
                history_len = st.number_input("历史对话轮数", 0, 20, 3)

        return llm_model, prompt_template, temperature, history_len


def render_mode_specific_config(dialogue_mode: str, api):
    """根据对话模式渲染差异化配置（非公共）"""
    if dialogue_mode == "知识库问答":
        with st.container(border=True):
            st.subheader("知识库配置", divider="gray")
            kb_list = api.list_knowledge_bases()
            selected_kb = st.selectbox("选择知识库：", kb_list, index=0)
            return {"selected_kb": selected_kb}

    elif dialogue_mode == "文件对话":
        with st.container(border=True):
            st.subheader("文件上传", divider="gray")
            uploaded_files = st.file_uploader("上传文件（支持PDF/Word）", accept_multiple_files=True)
            return {"uploaded_files": uploaded_files}

    elif dialogue_mode == "搜索引擎问答":
        with st.container(border=True):
            st.subheader("搜索配置", divider="gray")
            search_engine = st.selectbox("搜索引擎：", ["百度", "谷歌", "必应"])
            return {"search_engine": search_engine}

    else:
        return {}