import httpx
from fastapi import Body

from chat.chat_utils import get_model_worker_config
from configs.basic import HTTPX_DEFAULT_TIMEOUT
from configs.fastchat import get_controller_addr
from pages.api_utils import BaseResponse, get_api_logger

logger = get_api_logger()
# 获取运行中的模型列表
async def list_running_models() -> BaseResponse:
    controller_address = get_controller_addr()
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{controller_address}/list_models",
                timeout=HTTPX_DEFAULT_TIMEOUT,
            )
            models = resp.json()["models"]
            data = {m: get_model_config(m).data for m in models}
            return BaseResponse(data=data)
    except Exception as e:
        logger.error(f"list_running_models error: {e}")
        return BaseResponse(code=500, msg=str(e), data=None)


def get_model_config(model_name:str=Body(..., description="模型名称")) -> BaseResponse:
    '''
    获取LLM模型配置项（合并后的）
    '''
    config = {}
    # 删除ONLINE_MODEL配置中的敏感信息
    for k, v in get_model_worker_config(model_name=model_name).items():
        if not (k == "worker_class"
                or "key" in k.lower()
                or "secret" in k.lower()
                or k.lower().endswith("id")):
            config[k] = v

    return BaseResponse(data=config)