import os.path

from configs.basic import PROJECT_ROOT

TEMPERATURE = 0.7

MODEL_PATH = {
    "embed_model": {},
    "llm_model": {
        "DeepSeek-R1-Distill-Qwen-1.5B": os.path.join(PROJECT_ROOT, "models/DeepSeek-R1-Distill-Qwen-1.5B"),
        "chatglm3-6b": os.path.join(PROJECT_ROOT, "models/chatglm3-6b"),
        "Qwen3-4B": os.path.join(PROJECT_ROOT, "models/Qwen3-4B"),
    }
}