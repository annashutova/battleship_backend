from typing import Any, Dict

from fastapi import Depends
from fastapi.responses import ORJSONResponse

from webapp.api.game.router import game_router
from webapp.cache.get_game import get_game_by_user
from webapp.game.core import BattleShipGame


@game_router.get('/opponent_board')
async def get_player_board(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player = game.player

    board = game.opponent_map(player.user_id)

    return _prepare_response(
        {
            'ai_board': board,
        }
    )


@game_router.get('/player_board')
async def get_opponent_board(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    board = game.player_map()

    return _prepare_response(
        {
            'player_board': board,
        }
    )


def _prepare_response(data: Dict[str, Any]) -> ORJSONResponse:
    return ORJSONResponse(
        {
            'data': data,
        }
    )
