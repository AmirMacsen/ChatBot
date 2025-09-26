# 基础配置：独立于业务的核心参数
import os
from datetime import datetime
from typing import List

import torch

# 项目根路径（自动计算，避免硬编码）
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 日志配置
LOG_PATH = os.path.join(PROJECT_ROOT, "logs")
os.makedirs(LOG_PATH, exist_ok=True)  # 确保日志目录存在
LOG_VERBOSE = True
LOG_LEVEL = "INFO"  # 默认为INFO，quiet模式下改为ERROR

# 模型配置
LLM_MODELS: List[str] = ["DeepSeek-R1-Distill-Qwen-1.5B"]  # 默认LLM模型
EMBEDDING_MODEL = "m3e-base"
TEXT_SPLITTER_NAME = "RecursiveCharacterTextSplitter"

# 设备配置
LLM_DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
EMBEDDING_DEVICE = LLM_DEVICE

# 网络超时
HTTPX_DEFAULT_TIMEOUT = 30

# 项目版本
VERSION = "0.2.1"