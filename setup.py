import asyncio
import multiprocessing as mp
import signal
import sys
from contextlib import asynccontextmanager
from importlib import reload

from fastapi import FastAPI

from configs.fastchat import FSCHAT_MODEL_WORKERS
from core.api import run_app
from core import open_ai_api_server


def _set_app_event(app: FastAPI, started_event: mp.Event = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if started_event is not None:
            started_event.set()
        yield

    app.lifespan_context = lifespan


async def start_main_server():
    # 创建关闭事件
    shutdown_event = asyncio.Event()

    # 重载模块,修改pydantic的问题
    sys.modules["fastchat.server.openai_api_server"] = reload(open_ai_api_server)

    def signal_handler(signum, frame):
        signal_name = signal.Signals(signum).name
        print(f"\nReceived {signal_name} signal. Initiating graceful shutdown...")
        shutdown_event.set()

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    processes={}

    try:
        # 启动API服务器
        from multiprocessing import Process, Manager
        manager = Manager()

        # 启动controller服务
        controller_started = manager.Event()
        from core.controller import run_controller
        controller_process = Process(target=run_controller,kwargs={"log_level": "INFO",
                                                                   "started_event": controller_started})
        controller_process.start()
        processes["controller"] = controller_process

        # 等待controller启动
        await asyncio.get_event_loop().run_in_executor(None, controller_started.wait, 10)



        # 启动model_worker
        from core.model_worker import run_model_worker
        for model_name, config in FSCHAT_MODEL_WORKERS.items():
            model_worker_started = manager.Event()
            # 创建队列用于模型管理
            model_queue = manager.Queue()
            model_worker_process = Process(target=run_model_worker,
                                           kwargs={"model_name": model_name,
                                                   "log_level": "INFO",
                                                   "queue": model_queue,
                                                   "started_event": model_worker_started})
            model_worker_process.start()
            await asyncio.get_event_loop().run_in_executor(None, model_worker_started.wait, 10)
            processes[model_name] = model_worker_process


        # 启动openai_api
        from core.openai_api import run_openai_api
        openai_api_started = manager.Event()
        openai_api_process = Process(target=run_openai_api,
                                     kwargs={"log_level": "INFO",
                                             "started_event": openai_api_started})
        openai_api_process.start()
        processes["openai_api"] = openai_api_process
        await asyncio.get_event_loop().run_in_executor(None, openai_api_started.wait, 10)


        # 启动api服务
        from core.api import create_app
        api_started = manager.Event()
        api_process = Process(target=run_app,
                             kwargs={"started_event": api_started,
                                     "run_mode": "main"})
        api_process.start()
        processes["api"] = api_process
        await asyncio.get_event_loop().run_in_executor(None, api_started.wait, 10)


        print("Server is running. Press Ctrl+C to stop.")

        # 等待关闭信号
        await shutdown_event.wait()

        print("Shutting down...")

        # 优雅关闭API进程
        for process in processes.values():
            process.terminate()
            process.join(timeout=5)
            if process.is_alive():
                process.kill()
                process.join()

        print("Server stopped gracefully.")

    except Exception as e:
        print(f"Error occurred: {e}")
        return 1
    return 0


def main():
    if sys.version_info < (3, 10):
        loop = asyncio.get_event_loop()
    else:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        asyncio.set_event_loop(loop)
    loop.run_until_complete(start_main_server())

if __name__ == '__main__':
    main()