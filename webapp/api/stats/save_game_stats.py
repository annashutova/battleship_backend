from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from webapp.api.stats.router import stats_router
from webapp.cache.get_game import get_game_by_user
from webapp.crud.stats import save_game_data
from webapp.db.postgres import get_session
from webapp.game.core import BattleShipGame
from webapp.schema.stats import SaveDataResponse


@stats_router.post(
    '/save_data',
    response_model=SaveDataResponse,
)
async def save_data(
    session: AsyncSession = Depends(get_session),
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    if not game.finished:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Game has not been finished yet. Finish the game before saving data.',
        )

    ships_sank = len(list(filter(None, [ship.is_destroyed() for ship in game.player.board.ships])))
    ships_destroyed = len(list(filter(None, [ship.is_destroyed() for ship in game.ai.board.ships])))

    if game.winner is not None:
        winner_id = game.winner.user_id
    else:
        winner_id = None

    await save_game_data(session, game.player.user_id, game.player.user_id == winner_id, ships_sank, ships_destroyed)

    return ORJSONResponse(
        {
            'status': 'success',
        }
    )
