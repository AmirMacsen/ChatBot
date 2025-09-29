# 该文件封装了对api.py的请求，可以被不同的webui使用

from typing import *

from loguru import logger
from pydantic import BaseModel, Field

from configs.basic import PROJECT_ROOT, LLM_MODELS, HTTPX_DEFAULT_TIMEOUT
from configs.fastchat import get_api_server_addr
# 此处导入的配置为发起请求（如WEBUI）机器上的配置，主要用于为前端设置默认值。分布式部署时可以与服务器上的不同
from utils.http import set_httpx_config

set_httpx_config()

log_verbose = True


class BaseResponse(BaseModel):
    code: int = Field(200, description="API status code")
    msg: str = Field("success", description="API status message")
    data: Any = Field(None, description="API data")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
            }
        }


class ListResponse(BaseResponse):
    data: List[str] = Field(..., description="List of names")

    class Config:
        json_schema_extra = {
            "example": {
                "code": 200,
                "msg": "success",
                "data": ["doc1.docx", "doc2.pdf", "doc3.txt"],
            }
        }


# 优化版API请求封装，专注于核心功能
from typing import *
import httpx
import json
import os


class ApiRequest:
    '''
    简化版API请求封装，支持同步/异步调用
    专注于实现chat_chat和list_running_models核心功能
    '''

    def __init__(
            self,
            base_url: str = get_api_server_addr(),
            timeout: float = HTTPX_DEFAULT_TIMEOUT,
            use_async: bool = False,
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.use_async = use_async
        self._client = None

    @property
    def client(self):
        '''延迟初始化HTTP客户端，确保线程安全'''
        if self._client is None or (
                (self.use_async and self._client.is_closed)
                or (not self.use_async and getattr(self._client, 'is_closed', False))
        ):
            self._client = self._create_client()
        return self._client

    def _create_client(self):
        '''根据同步/异步模式创建对应的HTTP客户端'''
        if self.use_async:
            return httpx.AsyncClient(base_url=self.base_url, timeout=self.timeout)
        else:
            return httpx.Client(base_url=self.base_url, timeout=self.timeout)

    def close(self):
        '''关闭HTTP客户端释放资源'''
        if self._client:
            if self.use_async:
                import asyncio
                asyncio.create_task(self._client.aclose())
            else:
                self._client.close()
            self._client = None

    # 核心请求方法
    def request(self, method: str, url: str, **kwargs):
        '''统一请求入口，根据模式自动选择同步或异步请求'''
        # 处理stream参数，避免直接传递给request方法
        stream = kwargs.pop('stream', False)

        if self.use_async:
            return self._async_request(method, url, stream=stream, **kwargs)
        else:
            return self._sync_request(method, url, stream=stream, **kwargs)

    def _sync_request(self, method: str, url: str, stream: bool = False, **kwargs):
        '''同步HTTP请求实现'''
        try:
            if stream:
                # 使用httpx.stream进行流式请求
                return httpx.stream(method, f"{self.base_url}{url}", timeout=self.timeout, **kwargs)
            else:
                # 普通请求
                response = self.client.request(method, url, **kwargs)
                response.raise_for_status()  # 自动抛出HTTP错误
                return response
        except Exception as e:
            self._log_error(f"同步{method}请求失败: {url}", e)
            raise

    async def _async_request(self, method: str, url: str, stream: bool = False, **kwargs):
        '''异步HTTP请求实现'''
        try:
            if stream:
                # 使用client.stream进行异步流式请求
                return await self.client.stream(method, url, **kwargs)
            else:
                # 普通请求
                response = await self.client.request(method, url, **kwargs)
                response.raise_for_status()  # 自动抛出HTTP错误
                return response
        except Exception as e:
            self._log_error(f"异步{method}请求失败: {url}", e)
            raise

    # 便捷请求方法
    def get(self, url: str, **kwargs):
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs):
        return self.request("POST", url, **kwargs)

    # 流式响应处理
    def stream_to_generator(self, response_context, as_json: bool = False):
        '''将HTTP流式响应转换为可迭代的生成器'''
        if self.use_async:
            return self._async_stream_to_generator(response_context, as_json)
        else:
            return self._sync_stream_to_generator(response_context, as_json)

    def _sync_stream_to_generator(self, response_context, as_json: bool = False):
        '''同步流式响应处理'''
        try:
            with response_context as r:
                for chunk in r.iter_text():
                    if not chunk:  # 跳过空数据块
                        continue
                    yield self._process_chunk(chunk, as_json)
        except httpx.ConnectError as e:
            msg = f"无法连接API服务器，请确认服务已正常启动。({e})"
            logger.error(msg)
            yield {"code": 500, "msg": msg}
        except httpx.ReadTimeout as e:
            msg = f"API通信超时，请检查服务状态。({e})"
            logger.error(msg)
            yield {"code": 500, "msg": msg}
        except Exception as e:
            self._log_error("处理流式响应失败", e)
            yield {"code": 500, "msg": f"API通信遇到错误: {str(e)}"}

    async def _async_stream_to_generator(self, response_context, as_json: bool = False):
        '''异步流式响应处理'''
        try:
            async with response_context as r:
                async for chunk in r.aiter_text():
                    if not chunk:  # 跳过空数据块
                        continue
                    yield self._process_chunk(chunk, as_json)
        except httpx.ConnectError as e:
            msg = f"无法连接API服务器，请确认服务已正常启动。({e})"
            logger.error(msg)
            yield {"code": 500, "msg": msg}
        except httpx.ReadTimeout as e:
            msg = f"API通信超时，请检查服务状态。({e})"
            logger.error(msg)
            yield {"code": 500, "msg": msg}
        except Exception as e:
            self._log_error("处理流式响应失败", e)
            yield {"code": 500, "msg": f"API通信遇到错误: {str(e)}"}

    def _process_chunk(self, chunk: str, as_json: bool) -> Union[str, dict]:
        '''处理单个数据块，支持JSON解析和SSE格式'''
        if not as_json:
            return chunk

        try:
            # 处理SSE格式响应
            if chunk.startswith("data: "):
                # 去除data:前缀和末尾换行符
                return json.loads(chunk[6:].rstrip("\n"))
            elif chunk.startswith(":"):
                # 跳过SSE注释行
                return {}
            else:
                # 直接解析JSON
                return json.loads(chunk)
        except json.JSONDecodeError:
            logger.error(f"解析JSON失败: {chunk}")
            return {}

    def _log_error(self, message: str, exception: Exception):
        '''统一错误日志记录'''
        if log_verbose:
            logger.error(f'{exception.__class__.__name__}: {message}', exc_info=exception)
        else:
            logger.error(f'{exception.__class__.__name__}: {message}')

    # 核心业务功能
    def chat_chat(
            self,
            query: str,
            conversation_id: str = None,
            history: List[Dict] = None,
            stream: bool = True,
            model: str = None,
            temperature: float = None,
            max_tokens: int = None,
            prompt_name: str = "default",
            **kwargs,
    ):
        '''
        对话接口调用
        参数:
            query: 用户查询文本
            conversation_id: 对话ID
            history: 对话历史
            stream: 是否使用流式响应
            model: LLM模型名称
            temperature: 生成温度
            max_tokens: 最大生成长度
            prompt_name: 提示模板名称
        '''
        # 设置默认值
        if history is None:
            history = []
        if model is None and LLM_MODELS:
            model = LLM_MODELS[0]

        # 构建请求数据
        data = {
            "query": query,
            "conversation_id": conversation_id,
            "history": history,
            "stream": stream,
            "model_name": model,
            "prompt_name": prompt_name,
            **kwargs  # 允许额外参数
        }

        # 添加可选参数
        if temperature is not None:
            data["temperature"] = temperature
        if max_tokens is not None:
            data["max_tokens"] = max_tokens

        # 处理流式和非流式响应
        if stream:
            response = self.post("/chat/chat", json=data, stream=True)
            return self.stream_to_generator(response, as_json=True)
        else:
            response = self.post("/chat/chat", json=data)
            return response.json()

    def list_running_models(
            self,
    ) -> Dict:
        '''
        获取当前运行的模型列表
        返回:
            运行中的模型字典
        '''
        response = self.post("/llm_model/list_running_models")
        try:
            result = response.json()
            # 确保返回格式一致
            return result.get("data", {}) if isinstance(result, dict) else {}
        except Exception as e:
            self._log_error("解析模型列表失败", e)
            return {}


# 创建同步API实例
sync_api = ApiRequest(use_async=False)

# 创建异步API实例（如需使用异步功能）
async_api = ApiRequest(use_async=True)


def get_api_logger():
    logger_path = os.path.join(PROJECT_ROOT, "logs")
    if not os.path.exists(logger_path):
        os.makedirs(logger_path)
    logger.add(f"{logger_path}/api.log", rotation="500 MB", enqueue=True, compression="zip")
    return logger
