import multiprocessing as mp
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.llm_api import list_running_models
from chat.chat import chat
from configs.basic import VERSION


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

    # Tag: LLM Model Management
    app.post("/llm_model/list_running_models",
             tags=["LLM Model Management"],
             summary="列出当前已加载的模型",
             )(list_running_models)



def run_app(started_event: mp.Event, run_mode: str = None):
    """
    启动服务
    :param run_mode:
    :return:
    """
    import uvicorn
    from configs.fastchat import API_SERVER
    from utils.http import set_httpx_config

    set_httpx_config()
    app = create_app(run_mode=run_mode)
    started_event.set()  # 标记服务启动完成
    uvicorn.run(
        app,
        host=API_SERVER["host"],
        port=API_SERVER["port"],
    )


