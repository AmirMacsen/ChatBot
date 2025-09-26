import uuid
from typing import Dict

from db.models.message_model import MessageModel
from db.session import get_db_session


async def add_message_to_db(conversation_id: str, chat_type, query, response="", message_id=None,
                      metadata: Dict = {}):
    """
    新增消息记录
    """
    if not message_id:
        message_id = uuid.uuid4().hex
    async with get_db_session() as session:
        message = MessageModel(
            id=message_id,
            conversation_id=conversation_id,
            chat_type=chat_type,
            query=query,
            response=response,
            meta_data=metadata
        )
        session.add(message)
        await session.commit()
    return message.id

async def get_message_by_id(message_id):
    """
    根据id获取消息记录
    """
    async with get_db_session() as session:
        message = await session.get(MessageModel, message_id)
    return message

async def update_message_to_db(message_id, response: str = None, metadata: Dict = None):
    """
    更新已有的聊天记录
    """
    m = await get_message_by_id(message_id)
    if m is not None:
        if response is not None:
            m.response = response
        if isinstance(metadata, dict):
            m.meta_data = metadata
    async with get_db_session() as session:
            session.add(m)
            await session.commit()
            return m.id