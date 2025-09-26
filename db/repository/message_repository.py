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
