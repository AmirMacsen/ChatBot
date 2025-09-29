# openai api 服务：仅负责创建FastChat openapi-api的FastAPI实例
import sys
from fastapi import FastAPI, Body

from configs.fastchat import get_controller_addr, FSCHAT_OPENAI_API
from configs.basic import LOG_PATH
import fastchat.constants
import multiprocessing as mp

fastchat.constants.LOGDIR = LOG_PATH  # 全局日志目录配置


def create_openai_api_app(dispatch_method: str, log_level: str) -> FastAPI:
    """创建openai api 服务实例"""
    import fastchat.constants
    fastchat.constants.LOGDIR = LOG_PATH
    from fastchat.serve.openai_api_server import app, CORSMiddleware, app_settings
    from fastchat.utils import build_logger
    logger = build_logger("openai_api", "openai_api.log")
    logger.setLevel(log_level)

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    controller_address = get_controller_addr()
    sys.modules["fastchat.serve.openai_api_server"].logger = logger
    app_settings.controller_address = controller_address
    app_settings.api_keys = ""

    app.title = "FastChat OpeanAI API Server"
    return app


def run_openai_api(log_level: str, started_event: mp.Event) -> None:
    """Controller服务启动入口（与进程解耦）"""
    import uvicorn
    from configs.fastchat import FSCHAT_CONTROLLER
    from utils.http import set_httpx_config

    set_httpx_config()
    app = create_openai_api_app(
        dispatch_method=FSCHAT_CONTROLLER["dispatch_method"],
        log_level=log_level
    )
    started_event.set()  # 标记服务启动完成

    # 启动UVicorn服务
    uvicorn.run(
        app,
        host=FSCHAT_OPENAI_API["host"],
        port=FSCHAT_OPENAI_API["port"],
        log_level=log_level.lower()
    )