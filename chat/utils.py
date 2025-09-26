import asyncio
import os
from typing import Union, List, Tuple, Dict, Callable, Any, Literal, Optional, Awaitable

from langchain_community.chat_models import ChatOpenAI
from langchain_core.prompts import ChatMessagePromptTemplate
from pydantic import BaseModel, Field

from configs.basic import LLM_DEVICE
from configs.fastchat import get_openai_api_addr


async def wrap_done(fn: Awaitable, event: asyncio.Event):
    """Wrap an awaitable with a event to signal when it's done or an exception is raised."""
    try:
        await fn
    except Exception as e:
        import traceback
        print(traceback.format_exc())
    finally:
        # Signal the aiter to stop.
        event.set()


class History(BaseModel):
    """
    对话历史
    可从dict生成，如
    h = History(**{"role":"user","content":"你好"})
    也可转换为tuple，如
    h.to_msy_tuple = ("human", "你好")
    """
    role: str = Field(...)
    content: str = Field(...)

    def to_msg_tuple(self):
        return "ai" if self.role=="assistant" else "human", self.content

    def to_msg_template(self, is_raw=True) -> ChatMessagePromptTemplate:
        role_maps = {
            "ai": "assistant",
            "human": "user",
        }
        role = role_maps.get(self.role, self.role)
        if is_raw: # 当前默认历史消息都是没有input_variable的文本。
            content = "{% raw %}" + self.content + "{% endraw %}"
        else:
            content = self.content

        return ChatMessagePromptTemplate.from_template(
            content,
            "jinja2",
            role=role,
        )

    @classmethod
    def from_data(cls, h: Union[List, Tuple, Dict]) -> "History":
        if isinstance(h, (list,tuple)) and len(h) >= 2:
            h = cls(role=h[0], content=h[1])
        elif isinstance(h, dict):
            h = cls(**h)

        return h


def detect_device() -> Literal["cuda", "mps", "cpu"]:
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if torch.backends.mps.is_available():
            return "mps"
    except:
        pass
    return "cpu"


def llm_device(device: str = None) -> Literal["cuda", "mps", "cpu"]:
    device = device or LLM_DEVICE
    if device not in ["cuda", "mps", "cpu"]:
        device = detect_device()
    return device



def get_model_worker_config(model_name: str = None) -> dict:
    '''
    加载model worker的配置项。
    优先级:FSCHAT_MODEL_WORKERS[model_name] > ONLINE_LLM_MODEL[model_name] > FSCHAT_MODEL_WORKERS["default"]
    '''
    from configs.model import MODEL_PATH
    from configs.fastchat import FSCHAT_MODEL_WORKERS

    config = FSCHAT_MODEL_WORKERS.get("default", {}).copy()
    config.update(FSCHAT_MODEL_WORKERS.get(model_name, {}).copy())

    # 本地模型加载
    if model_name in MODEL_PATH["llm_model"]:
        path = MODEL_PATH["llm_model"][model_name]
        config["model_path"] = path
        if path and os.path.isdir(path):
            config["model_path_exists"] = True
        config["device"] = llm_device(config.get("device"))
    return config


def get_chat_model(model_name: str,
        temperature: float,
        max_tokens: int = None,
        streaming: bool = True,
        callbacks: List[Callable] = [],
        verbose: bool = True,
        **kwargs: Any,
) -> ChatOpenAI:
    """
    获取ChatOpenAI模型
    """
    # 1. 根据模型名称获取模型配置
    model_config = get_model_worker_config(model_name)
    model = ChatOpenAI(
        streaming=streaming,
        verbose=verbose,
        callbacks=callbacks,
        openai_api_key=model_config.get("api_key", "EMPTY"),
        openai_api_base=model_config.get("api_base_url", get_openai_api_addr()),
        model_name=model_name,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_proxy=model_config.get("openai_proxy"),
        request_timeout=300,  # 增加超时时间到300秒
        max_retries=3,        # 增加重试次数
        **kwargs
    )
    return model


def get_prompt_template(type: str, name: str) -> Optional[str]:
    '''
    从prompt_config中加载模板内容
    type: "llm_chat","agent_chat","knowledge_base_chat","search_engine_chat"的其中一种，如果有新功能，应该进行加入。
    '''

    from configs import prompt
    import importlib
    # 强制动态加载，避免修改配置文件后，重启服务。
    importlib.reload(prompt)
    return prompt.PROMPT_TEMPLATES[type].get(name)