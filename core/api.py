import multiprocessing as mp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app(run_mode: str = None):
    app = FastAPI(
        title="ChatBot API Server",
        version=VERSION
    )
    # Add CORS middleware to allow all origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    mount_app_routes(app, run_mode=run_mode)
    return app


def mount_app_routes(app: FastAPI, run_mode: str = None):
    """
    挂载接口
    :param app:
    :param run_mode:
    :return:
    """

    # Tag: Chat
    app.post("/chat/chat",
             tags=["Chat"],
             summary="与llm模型对话(通过LLMChain)",
             )(chat)


def run_app(started_event: mp.Event, run_mode: str = None):
    """
    启动服务
    :param run_mode:
    :return:
    """
    import uvicorn
    from configs.fastchat import API_SERVER
    app = create_app(run_mode=run_mode)
    started_event.set()  # 标记服务启动完成
    uvicorn.run(
        app,
        host=API_SERVER["host"],
        port=API_SERVER["port"],
    )


