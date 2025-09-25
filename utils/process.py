# 进程管理工具：封装进程创建、启动、终止等重复逻辑
import multiprocessing as mp
from multiprocessing import Process
from typing import Callable, Dict, Optional, Any
from configs.basic import LOG_PATH, LOG_LEVEL


class ProcessManager:
    """进程管理器：统一管理所有服务进程"""

    def __init__(self):
        self.processes: Dict[str, Process] = {}  # 进程注册表：{服务名: 进程对象}
        self.manager = mp.Manager()

    def create_process(
            self,
            name: str,
            target: Callable,
            kwargs: Optional[Dict[str, Any]] = None,
            daemon: bool = True
    ) -> Process:
        """创建进程（自动添加启动事件）"""
        kwargs = kwargs or {}
        # 统一添加启动事件（用于等待服务就绪）
        started_event = self.manager.Event()
        kwargs["started_event"] = started_event

        process = Process(
            target=target,
            name=name,
            kwargs=kwargs,
            daemon=daemon
        )
        self.processes[name] = process
        return process, started_event

    def start_process(self, name: str) -> Optional[mp.Event]:
        """启动指定进程并返回启动事件"""
        process = self.processes.get(name)
        if not process:
            raise ValueError(f"Process {name} not found")
        process.start()
        # 补充进程PID到名称中（方便日志排查）
        process.name = f"{process.name} (PID: {process.pid})"
        return process._kwargs.get("started_event")

    def terminate_process(self, name: str) -> None:
        """终止指定进程"""
        process = self.processes.get(name)
        if not process:
            return
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)  # 等待5秒，避免僵尸进程
        del self.processes[name]

    def terminate_all(self) -> None:
        """终止所有进程"""
        for name in list(self.processes.keys()):
            self.terminate_process(name)


def get_log_level(quiet: bool) -> str:
    """根据quiet参数获取日志级别"""
    return "ERROR" if quiet else LOG_LEVEL