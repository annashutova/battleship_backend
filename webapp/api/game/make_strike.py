from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette import status

from webapp.api.game.router import game_router
from webapp.cache.cache import redis_set
from webapp.cache.get_game import get_game_by_user
from webapp.game.core import BattleShipGame, Player
from webapp.schema.strike import StrikeCoord


@game_router.post('/player_strike')
async def player_strike(
    body: StrikeCoord,
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player: Player = game.player
    try:
        result = game.player_strike(body.coord)
        ai_board = game.opponent_map(player.user_id)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    is_finished = game.ai.board.is_finished()

    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    return _prepare_response(
        {
            'status': result,
            'ai_board': ai_board,
            'finished': is_finished,
        }
    )


@game_router.post('/ai_strike')
async def ai_strike(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player = game.player

    try:
        result = game.ai_strike()
        player_board = game.player_map()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    is_finished = player.board.is_finished()

    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    return _prepare_response(
        {
            'status': result,
            'player_board': player_board,
            'finished': is_finished,
        }
    )


def _prepare_response(data: Dict[str, Any]) -> ORJSONResponse:
    return ORJSONResponse(
        {
            'data': data,
        }
    )
