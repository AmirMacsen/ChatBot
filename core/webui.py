import json
import os
import subprocess
import time

import requests
import streamlit as st
from streamlit_option_menu import option_menu

from configs.basic import PROJECT_ROOT, VERSION
from configs.fastchat import WEBUI_SERVER
import multiprocessing as mp

from pages.dialog import dialogue_page
from pages.api_utils import sync_api


def run_webui(started_event: mp.Event = None, run_mode: str = None):
    from utils.http import set_httpx_config
    set_httpx_config()

    host = WEBUI_SERVER["host"]
    port = WEBUI_SERVER["port"]

    webui_file = os.path.join(PROJECT_ROOT,"core","webui.py")
    cmd = ["streamlit", "run", webui_file,
           "--server.address", host,
           "--server.port", str(port),
           "--theme.base", "light",
           "--theme.primaryColor", "#165dff",
           "--theme.secondaryBackgroundColor", "#f5f5f5",
           "--theme.textColor", "#000000",
           ]
    if run_mode == "lite":
        cmd += [
            "--",
            "lite",
        ]
    p = subprocess.Popen(cmd, shell=os.name == "nt")
    started_event.set()
    p.wait()


def response_generator(data):
    """处理模型响应并流式输出"""
    try:
        # 构建API请求
        url = "http://127.0.0.1:7861/chat/chat"
        headers = {'Content-Type': 'application/json'}
        request_data = {
            "query": data.get("text"),
            "conversation_id": "",
            "history_len": -1,
            "history": [
            ],
            "stream": False,
            "model_name": "DeepSeek-R1-Distill-Qwen-1.5B",
            "temperature": 0.7,
            "max_tokens": 512,
            "prompt_name": "default"
        }

        # 确保启用流式请求
        response = requests.post(url, json=request_data, headers=headers, stream=True, timeout=30)
        response.raise_for_status()

        # 用于存储累积的文本
        buffer = ""
        last_output = ""

        # 逐块处理响应
        for chunk in response.iter_content(chunk_size=None):
            if chunk:
                # 解码当前块
                chunk_str = chunk.decode('utf-8', errors='ignore')
                buffer += chunk_str

                # 检查是否包含完整的JSON对象
                if '}' in buffer and '{' in buffer:
                    try:
                        # 尝试提取JSON对象
                        start_idx = buffer.find('{')
                        end_idx = buffer.rfind('}') + 1
                        json_str = buffer[start_idx:end_idx]

                        # 更新buffer，保留剩余部分
                        buffer = buffer[end_idx:]

                        # 解析JSON
                        data = json.loads(json_str)

                        # 提取answer或text字段
                        text = data.get('answer', '') or data.get('text', '')

                        # 逐字输出新内容
                        if text and text != last_output:
                            # 找出新增的字符
                            new_chars = text[len(last_output):]
                            for char in new_chars:
                                yield char
                                time.sleep(0.02)  # 控制字符输出速度
                            last_output = text
                    except json.JSONDecodeError:
                        # JSON解析失败，继续累积
                        pass
                    except Exception as e:
                        yield f"处理响应块时发生错误: {str(e)}"
            else:
                # 无更多数据，退出循环
                break

        # 处理最后剩余的buffer内容
        if buffer.strip():
            for char in buffer:
                yield char
                time.sleep(0.02)

        # 如果没有任何输出，返回错误信息
        if last_output == "" and buffer == "":
            yield "未获取到响应内容，请检查后端服务是否正常运行。"
    except requests.exceptions.ConnectionError:
        yield "无法连接到后端服务，请确认http://127.0.0.1:7861服务是否正常启动。"
    except requests.exceptions.Timeout:
        yield "请求超时，请检查后端服务响应是否正常。"
    except Exception as e:
        yield f"发生错误: {str(e)}"

def main():
    st.set_page_config(
        "ChatBot WebUI",
        os.path.join("img", "logo.png"),
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://github.com/chatchat-space/Langchain-Chatchat',
            'Report a bug': "https://github.com/chatchat-space/Langchain-Chatchat/issues",
            'About': f"""欢迎使用 Langchain-Chatchat WebUI {VERSION}！"""
        }
    )

    if "history" not in st.session_state:
        st.session_state.history = []

    pages = {
        "对话": {
            "icon": "chat",
            "func": dialogue_page,
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
                "logo.png"
            ),
            use_container_width=True
        )
        st.caption(
            f"""<p align="right">当前版本：{VERSION}</p>""",
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
        api = sync_api
    if selected_page in pages:
        pages[selected_page]["func"](api=api, is_lite=True)


if __name__ == "__main__":
    main()