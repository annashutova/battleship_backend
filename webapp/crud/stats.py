from datetime import datetime
from typing import Any, Optional, Tuple

from sqlalchemy import Row, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.middleware.metrics import integration_latency
from webapp.models.sirius.game import Game


@integration_latency
async def get_statistics(
    session: AsyncSession,
    start_date: datetime,
    end_date: datetime,
    user_id: int,
) -> Optional[Row[Tuple[Any, ...]]]:
    query = select(
        func.count(func.nullif(Game.won == True, False)),
        func.count(func.nullif(Game.won == False, False)),
        func.coalesce(func.sum(Game.ships_sank), 0),
        func.coalesce(func.sum(Game.ships_destroyed), 0),
    ).filter(Game.timestamp >= start_date, Game.timestamp <= end_date, Game.user_id == user_id)

    return (await session.execute(query)).fetchone()


@integration_latency
async def save_game_data(
    session: AsyncSession,
    user_id: int,
    won: bool,
    ships_sank: int,
    ships_destroyed: int,
) -> None:
    await session.execute(
        insert(Game)
        .values(
            user_id=user_id,
            won=won,
            ships_sank=ships_sank,
            ships_destroyed=ships_destroyed,
        )
        .on_conflict_do_nothing()
    )
    await session.commit()
