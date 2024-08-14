from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from .models import Base, engine


class DatabaseManager:
    def __init__(self, engine):
        self.engine = engine
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def init_models(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)

    async def get_session(self):
        async with self.async_session() as session:
            yield session

    async def close(self):
        await self.engine.dispose()

database = DatabaseManager(engine)
