from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.middleware.metrics import integration_latency
from webapp.models.sirius.user import User
from webapp.schema.user import UserInfo


@integration_latency
async def get_user(session: AsyncSession, user_info: UserInfo) -> User | None:
    return (
        await session.scalars(
            select(User).where(
                User.username == user_info.username,
            )
        )
    ).one_or_none()


@integration_latency
async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    return (
        await session.scalars(
            select(User).where(
                User.id == user_id,
            )
        )
    ).one_or_none()


@integration_latency
async def create_user(session: AsyncSession, user_info: UserInfo) -> User | None:
    async with session.begin_nested():
        query = insert(User).values(user_info.model_dump())
        result = await session.execute(query)
        await session.commit()
    inserted_id = result.inserted_primary_key[0]
    return await get_user_by_id(session, inserted_id)
