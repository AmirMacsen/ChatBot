from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base, DeclarativeMeta
from sqlalchemy.orm import sessionmaker

from configs.store import get_database_url,DATABASE_TYPE


engine = create_async_engine(
    get_database_url(database_type=DATABASE_TYPE),
    echo=True,
    pool_size=10,
    max_overflow=20,
    pool_timeout=10,
    pool_recycle=3600,
    pool_pre_ping=True,
)

AsyncSessionFactory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    autoflush=True,
    expire_on_commit=False,
)

Base: DeclarativeMeta = declarative_base()
from db.models import conversation_model
from db.models import message_model
from db.models import knowledge_base_model
from db.models import knowledge_file_model
from db.models import knowledge_metadata_model
