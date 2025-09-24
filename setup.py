import asyncio
import multiprocessing as mp
import signal
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from server.api_server.server_app import create_app


def _set_app_event(app: FastAPI, started_event: mp.Event = None):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        if started_event is not None:
            started_event.set()
        yield

    app.lifespan_context = lifespan

def start_api_server(started_event: mp.Event = None,):
    app = create_app()
    _set_app_event(app, started_event)
    uvicorn.run(app, host="0.0.0.0", port=8000)

def start_web_server(started_event: mp.Event = None,):
    app = create_app()
    _set_app_event(app, started_event)
    uvicorn.run(app, host="0.0.0.0", port=8001)

async def start_main_server():
    def handler(signal_name):
        def f(signal_received, frame):
            raise KeyboardInterrupt(f"{signal_name} received")
        return f

    # 接收信号，触发handler函数
    signal.signal(signal.SIGINT, handler("SIGINT"))
    signal.signal(signal.SIGTERM, handler("SIGTERM"))

    # 设置多进程创建的方式， 默认是 fork， 这里改为 spawn
    # fork方式：创建子进程时，操作系统完全复制当前父进程的地址空间，子进程从父进程fork之后的代码开始执行
    # spawn方式：创建子进程时，创建一个全新的地址空间，仅仅继承一些环境变量之类的参数
    mp.set_start_method('spawn')
    # 创建一个进程管理器
    manager = mp.Manager()

    processes = dict()

    # api服务事件监听
    api_started = manager.Event()
    process = mp.Process(
        target=start_api_server,
        name="API Server",
        kwargs={
            "started_event": api_started,
        },
        daemon=False

    )

    processes["api"] = process


    # web服务事件监听
    web_started = manager.Event()
    process = mp.Process(
        target=start_web_server,
        name="Web Server",
        kwargs={
            "started_event": web_started,
        },
        daemon=False
    )
    processes["web"] = process
    try:
        ## 启动服务
        if p:=processes.get("api"):
            p.start()
            p.name = f"{p.name} ({p.pid})"
            # 等待服务启动
            api_started.wait(timeout=10) 

        if p:=processes.get("web"):
            p.start()
            p.name = f"{p.name} ({p.pid})"
            web_started.wait(timeout=10)

        # 等待所有进程都退出
        for p in processes.values():
            p.join()

            if not p.is_alive():
                processes.pop(p.name)
    except Exception as e:
        import traceback
        print(traceback.format_exc())
    finally:
        for p in processes.values():
            if p.is_alive():
                p.terminate()


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