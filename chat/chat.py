import asyncio
import json
from typing import Union, List, Optional, AsyncIterator

from fastapi import Body
from langchain.callbacks import AsyncIteratorCallbackHandler
from langchain.chains.llm import LLMChain
from langchain_core.prompts import PromptTemplate
from sse_starlette.sse import EventSourceResponse

from callback_handler.conversation_callback_handler import ConversationCallbackHandler
from chat.chat_utils import History, get_chat_model, get_prompt_template, wrap_done
from configs.basic import LLM_MODELS
from configs.model import TEMPERATURE
from db.repository.message_repository import add_message_to_db


async def chat(query: str = Body(..., description="用户输入", examples=["恼羞成怒"]),
               conversation_id: str = Body("", description="对话框ID"),
               history_len: int = Body(-1, description="从数据库中取历史消息的数量"),
               history: Union[int, List[History]] = Body([],
                                                         description="历史对话，设为一个整数可以从数据库中读取历史消息",
                                                         examples=[[
                                                             {"role": "user",
                                                              "content": "我们来玩成语接龙，我先来，生龙活虎"},
                                                             {"role": "assistant", "content": "虎头虎脑"}]]
                                                         ),
               stream: bool = Body(False, description="流式输出"),
               model_name: str = Body(LLM_MODELS[0], description="LLM 模型名称。"),
               temperature: float = Body(TEMPERATURE, description="LLM 采样温度", ge=0.0, le=2.0),
               max_tokens: Optional[int] = Body(None, description="限制LLM生成Token数量，默认None代表模型最大值"),
               # top_p: float = Body(TOP_P, description="LLM 核采样。勿与temperature同时设置", gt=0.0, lt=1.0),
               prompt_name: str = Body("default", description="使用的prompt模板名称(在configs/prompt.py中配置)"),
               ):
    async def chat_iterator():
        callback = AsyncIteratorCallbackHandler()
        callbacks = [callback]
        try:
            message_id = await add_message_to_db(conversation_id, "llm_chat", query)
            conversation_callback = ConversationCallbackHandler(
                conversation_id, message_id, "llm_chat", query
            )
            callbacks.append(conversation_callback)

            model = get_chat_model(model_name=model_name, temperature=temperature,
                                   max_tokens=max_tokens, callbacks=callbacks)
            prompt = get_prompt_template("llm_chat", prompt_name)
            # 创建PromptTemplate对象
            prompt_template = PromptTemplate.from_template(prompt)
            # 使用PromptTemplate对象创建LLMChain
            llm_chain = LLMChain(
                llm=model,
                prompt=prompt_template,
            )
            if stream:
                # 流式模式
                acall_task = asyncio.create_task(wrap_done(
                    llm_chain.acall({"input": query}),
                    callback.done),
                )
                async for token in callback.aiter():
                    yield json.dumps({"text": token, "message_id": message_id}, ensure_ascii=False)
                await acall_task
            else:
                # 非流式模式
                result = await llm_chain.acall({"input": query})
                answer = result.get("text", "")
                yield json.dumps({"text": answer, "message_id": message_id}, ensure_ascii=False)
        except asyncio.CancelledError:
            if acall_task:
                acall_task.cancel()
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            yield json.dumps({"text": f"模型调用出错: {str(e)}", "message_id": ""}, ensure_ascii=False)

    return EventSourceResponse(chat_iterator())

