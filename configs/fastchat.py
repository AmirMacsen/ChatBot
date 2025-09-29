# FastChat相关服务配置：端口、地址等
import os.path
from typing import Dict, Optional

from configs.basic import PROJECT_ROOT

# Controller配置
FSCHAT_CONTROLLER: Dict = {
    "host": "localhost",
    "port": 21001,
    "dispatch_method": "shortest_queue"
}

# OpenAI API适配层配置
FSCHAT_OPENAI_API: Dict = {
    "host": "localhost",
    "port": 8888,
    "api_keys": []  # 暂不支持API密钥验证
}

# Model Worker配置（按模型区分，支持多模型）
FSCHAT_MODEL_WORKERS: Dict = {
    "DeepSeek-R1-Distill-Qwen-1.5B": {
        "host": "localhost",
        "port": 21002,
        "model_path": os.path.join(PROJECT_ROOT, "models/DeepSeek-R1-Distill-Qwen-1.5B"),
        "device": "cuda",
        "num_gpus": 1,
        "max_gpu_memory": "22GiB",
        "online_api": False,
        "worker_class": None
    },
    # "bge-large-zh-v1.5": {
    #     "host": "localhost",
    #     "port": 21003,
    #     "model_path": os.path.join(PROJECT_ROOT, "models/bge-large-zh-v1.5"),
    #     "device": "cuda",
    #     "num_gpus": 1,
    #     "max_gpu_memory": "22GiB",
    #     "online_api": False,
    #     "worker_class": None
    # },
    # "chatglm3-6b": {
    #     "host": "localhost",
    #     "port": 21004,
    #     "model_path": os.path.join(PROJECT_ROOT, "models/chatglm3-6b"),
    #     "device": "cuda",
    #     "num_gpus": 1,
    #     "max_gpu_memory": "22GiB",
    #     "online_api": False,
    #     "worker_class": None
    # },
    # "Qwen3-4B": {
    #     "host": "localhost",
    #     "port": 21003,
    #     "model_path": os.path.join(PROJECT_ROOT, "models/Qwen3-4B"),
    #     "device": "cuda",
    #     "num_gpus": 1,
    #     "max_gpu_memory": "22GiB",
    #     "online_api": False,
    #     "load_in_8bit": True,
    #     "worker_class": None,
    #     "trust_remote_code": True
    # }

}

# 原生服务配置
API_SERVER: Dict = {
    "host": "localhost",
    "port": 7861
}

WEBUI_SERVER: Dict = {
    "host": "localhost",
    "port": 7860
}

# 服务地址生成工具函数（避免重复拼接）
def get_controller_addr() -> str:
    return f"http://{FSCHAT_CONTROLLER['host']}:{FSCHAT_CONTROLLER['port']}"

def get_model_worker_addr(model_name: str) -> str:
    config = FSCHAT_MODEL_WORKERS.get(model_name)
    if not config:
        raise ValueError(f"Model {model_name} not found in FSCHAT_MODEL_WORKERS")
    return f"http://{config['host']}:{config['port']}"

def get_openai_api_addr() -> str:
    return f"http://{FSCHAT_OPENAI_API['host']}:{FSCHAT_OPENAI_API['port']}/v1"

def get_api_server_addr() -> str:
    return f"http://{API_SERVER['host']}:{API_SERVER['port']}"

def get_webui_addr() -> str:
    return f"http://{WEBUI_SERVER['host']}:{WEBUI_SERVER['port']}"