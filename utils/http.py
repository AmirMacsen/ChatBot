# HTTP工具：统一HTTP客户端配置
import httpx
from configs.basic import HTTPX_DEFAULT_TIMEOUT

def get_httpx_client() -> httpx.Client:
    """获取统一配置的HTTP客户端"""
    return httpx.Client(
        timeout=HTTPX_DEFAULT_TIMEOUT,
        follow_redirects=True
    )

def set_httpx_config() -> None:
    """全局HTTPX配置（如超时、连接池）"""
    httpx._config.DEFAULT_TIMEOUT = HTTPX_DEFAULT_TIMEOUT