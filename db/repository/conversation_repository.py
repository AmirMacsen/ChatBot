import uuid

from db.models.conversation_model import ConversationModel
from db.session import get_db_session


async def add_conversation_to_db(chat_type, name="", conversation_id=None):
    """
    新增聊天记录
    :param chat_type:
    :param name:
    :param conversation_id:
    :return:
    """
    if not conversation_id:
        conversation_id = uuid.uuid4().hex
    async with get_db_session() as session:
        conversation = ConversationModel(
            id=conversation_id,
            chat_type=chat_type,
            name=name,
        )
        session.add(conversation)
        await session.commit()
    return conversation.id
