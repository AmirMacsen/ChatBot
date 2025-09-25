# Controller服务：仅负责创建FastChat Controller的FastAPI实例
import sys

from fastapi import FastAPI, Body
from fastchat.serve.controller import app as base_app, Controller
from utils.http import get_httpx_client
from configs.basic import LOG_PATH
import fastchat.constants
import multiprocessing as mp

fastchat.constants.LOGDIR = LOG_PATH  # 全局日志目录配置


def create_controller_app(dispatch_method: str, log_level: str) -> FastAPI:
    """创建Controller服务实例"""
    # 初始化Controller核心逻辑
    controller = Controller(dispatch_method)
    # 挂载Controller实例到APP
    sys.modules["fastchat.serve.controller"].controller = controller # 挂载Controller到APP
    base_app._controller = controller

    # 添加模型切换接口
    @base_app.post("/release_worker")
    def release_worker(
            model_name: str = Body(..., description="待释放模型名称"),
            new_model_name: str = Body(None, description="切换目标模型名称"),
            keep_origin: bool = Body(False, description="是否保留原模型")
    ):
        available_models = controller.list_models()
        # 基础校验
        if model_name not in available_models:
            return {"code": 500, "msg": f"Model {model_name} not available"}

        # 执行释放/切换逻辑
        worker_addr = controller.get_worker_address(model_name)
        with get_httpx_client() as client:
            resp = client.post(
                f"{worker_addr}/release",
                json={"new_model_name": new_model_name, "keep_origin": keep_origin}
            )
        if resp.status_code != 200:
            return {"code": 500, "msg": f"Failed to release {model_name}"}

        return {"code": 200, "msg": f"Success to handle {model_name}"}

    base_app.title = "FastChat Controller"
    return base_app


def run_controller(log_level: str, started_event: mp.Event) -> None:
    """Controller服务启动入口（与进程解耦）"""
    import uvicorn
    from configs.fastchat import FSCHAT_CONTROLLER
    from utils.http import set_httpx_config

    set_httpx_config()
    app = create_controller_app(
        dispatch_method=FSCHAT_CONTROLLER["dispatch_method"],
        log_level=log_level
    )
    started_event.set()  # 标记服务启动完成

    # 启动UVicorn服务
    uvicorn.run(
        app,
        host=FSCHAT_CONTROLLER["host"],
        port=FSCHAT_CONTROLLER["port"],
        log_level=log_level.lower()
    )