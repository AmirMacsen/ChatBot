import os.path

from configs.basic import PROJECT_ROOT

MODEL_ROOT_PATH = ""

# 选用的 Embedding 名称
EMBEDDING_MODEL = "bge-large-zh-v1.5"

# Embedding 模型运行设备。设为 "auto" 会自动检测(会有警告)，也可手动设定为 "cuda","mps","cpu","xpu" 其中之一。
EMBEDDING_DEVICE = "auto"

# 选用的reranker模型
RERANKER_MODEL = "bge-reranker-large"
# 是否启用reranker模型
USE_RERANKER = False
RERANKER_MAX_LENGTH = 1024

# 如果需要在 EMBEDDING_MODEL 中增加自定义的关键字时配置
EMBEDDING_KEYWORD_FILE = "keywords.txt"
EMBEDDING_MODEL_OUTPUT_PATH = "output"

# 要运行的 LLM 名称，可以包括本地模型和在线模型。列表中本地模型将在启动项目时全部加载。
# 列表中第一个模型将作为 API 和 WEBUI 的默认模型。
# 在这里，我们使用目前主流的两个离线模型，其中，chatglm3-6b 为默认加载模型。
# 如果你的显存不足，可使用 Qwen-1_8B-Chat, 该模型 FP16 仅需 3.8G显存。
Agent_MODEL = None

# LLM 模型运行设备。设为"auto"会自动检测(会有警告)，也可手动设定为 "cuda","mps","cpu","xpu" 其中之一。
LLM_DEVICE = "auto"

HISTORY_LEN = 3

MAX_TOKENS = 2048

TEMPERATURE = 0.7

ONLINE_LLM_MODEL = {
    "openai-api": {
        "model_name": "gpt-4",
        "api_base_url": "https://api.openai.com/v1",
        "api_key": "",
        "openai_proxy": "",
    },
}

MODEL_PATH = {
    "embed_model": {},
    "llm_model": {
        "DeepSeek-R1-Distill-Qwen-1.5B": os.path.join(PROJECT_ROOT, "models/DeepSeek-R1-Distill-Qwen-1.5B"),
        "bge-large-zh-v1.5": os.path.join(PROJECT_ROOT, "models/bge-large-zh-v1.5"),
        "chatglm3-6b": os.path.join(PROJECT_ROOT, "models/chatglm3-6b"),
        "Qwen3-4B": os.path.join(PROJECT_ROOT, "models/Qwen3-4B"),
    }
}