# Model Worker服务：仅负责创建Worker的FastAPI实例
from fastapi import FastAPI, Body
from configs.fastchat import FSCHAT_MODEL_WORKERS, get_controller_addr, get_model_worker_addr
from configs.basic import LOG_PATH
import fastchat.constants
import multiprocessing as mp

fastchat.constants.LOGDIR = LOG_PATH

def create_model_worker_app(model_name: str, log_level: str, queue: mp.Queue) -> FastAPI:
    """创建Model Worker服务实例（支持本地模型/在线API）"""
    config = FSCHAT_MODEL_WORKERS[model_name]
    kwargs = {
        "model_names": [model_name],
        "controller_address": get_controller_addr(),
        "worker_address": get_model_worker_addr(model_name),
        **config  # 合并模型专属配置
    }

    # 1. 在线API Worker（如智谱）
    if config["online_api"] and config["worker_class"]:
        from fastchat.serve.base_model_worker import app as base_app
        worker = config["worker_class"](
            model_names=kwargs["model_names"],
            controller_addr=kwargs["controller_address"],
            worker_addr=kwargs["worker_address"]
        )
        base_app._worker = worker

    # 2. 本地VLLM Worker
    # elif config.get("infer_turbo") == "vllm":
    #     from fastchat.serve.vllm_worker import app as base_app, VLLMWorker
    #     from vllm import AsyncLLMEngine
    #     from vllm.engine.arg_utils import AsyncEngineArgs
    #
    #     # VLLM引擎配置（简化默认参数，保留核心配置）
    #     engine_args = AsyncEngineArgs(
    #         model=config["model_path"],
    #         tensor_parallel_size=config["num_gpus"],
    #         gpu_memory_utilization=0.9,
    #         max_num_seqs=256
    #     )
    #     engine = AsyncLLMEngine.from_engine_args(engine_args)
    #     worker = VLLMWorker(
    #         controller_addr=kwargs["controller_address"],
    #         worker_addr=kwargs["worker_address"],
    #         model_path=config["model_path"],
    #         model_names=kwargs["model_names"],
    #         llm_engine=engine
    #     )
    #     base_app._worker = worker

    # 3. 普通本地模型Worker
    else:
        from fastchat.serve.model_worker import app as base_app, ModelWorker, GptqConfig, AWQConfig

        # 量化配置（简化参数）
        gptq_config = GptqConfig(
            ckpt=config["model_path"],
            wbits=config.get("gptq_wbits", 16),
            groupsize=config.get("gptq_groupsize", -1)
        )
        awq_config = AWQConfig(
            ckpt=config["model_path"],
            wbits=config.get("awq_wbits", 16),
            groupsize=config.get("awq_groupsize", -1)
        )

        worker = ModelWorker(
            worker_id=model_name,
            limit_worker_concurrency=config.get("limit_worker_concurrency", 1),
            no_register=config.get("no_register", False),
            controller_addr=kwargs["controller_address"],
            worker_addr=kwargs["worker_address"],
            model_path=config["model_path"],
            model_names=kwargs["model_names"],
            device=config["device"],
            num_gpus=config["num_gpus"],
            max_gpu_memory=config["max_gpu_memory"],
            gptq_config=gptq_config,
            awq_config=awq_config
        )
        base_app._worker = worker

    # 添加模型释放接口
    @base_app.post("/release")
    def release_model(
        new_model_name: str = Body(None),
        keep_origin: bool = Body(False)
    ):
        if keep_origin and new_model_name:
            queue.put(("start", model_name, new_model_name))
        elif new_model_name:
            queue.put(("replace", model_name, new_model_name))
        else:
            queue.put(("stop", model_name, None))
        return {"code": 200, "msg": "Received release command"}

    base_app.title = f"FastChat Model Worker ({model_name})"
    return base_app

def run_model_worker(
    model_name: str,
    log_level: str,
    queue: mp.Queue,
    started_event: mp.Event
) -> None:
    """Model Worker服务启动入口"""
    import uvicorn
    from configs.fastchat import FSCHAT_MODEL_WORKERS
    from utils.http import set_httpx_config

    set_httpx_config()
    app = create_model_worker_app(model_name, log_level, queue)
    started_event.set()

    # 启动UVicorn服务
    config = FSCHAT_MODEL_WORKERS[model_name]
    print(f"Starting model worker for {model_name}...")
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        log_level=log_level.lower()
    )
    print(f"Model worker for {model_name} stopped.")