from datetime import datetime

from sqlalchemy import Column, Integer


class BaseModel:
    """
    BaseModel
    """
    id = Column(Integer, primary_key=True, index=True, comment="主键ID")
    created_at = Column(Integer, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(Integer, default=datetime.utcnow, comment="更新时间")
    create_by = Column(Integer, default=None, comment="创建人")
    update_by = Column(Integer, default=None, comment="更新人")