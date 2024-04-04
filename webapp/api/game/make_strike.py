from typing import Dict, Any

from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette import status

from webapp.api.game.router import game_router
from webapp.cache.get_game import get_game_by_user

from webapp.game.core import Player
from webapp.game.core import BattleShipGame
from webapp.schema.strike import StrikeCoord

from webapp.cache.cache import redis_set
from pprint import pprint

TEST = None

@game_router.post('/player_strike')
async def player_strike(
    body: StrikeCoord,
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    global TEST
    player: Player = game.player
    print(game == game)
    print(game == TEST)
    try:
        result = game.player_strike(body.coord)
        ai_board = game.opponent_map(player.user_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )
    try:
        print(f'test hit: {player.board.board[body.coord[1]][body.coord[0]].ship.hp}')
    except Exception:
        pass

    pprint(game.model_dump())
    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    TEST = game
    return _prepare_response(
        {
            'status': result,
            'ai_board': ai_board,
        }
    )

@game_router.post('/ai_strike')
async def ai_strike(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player = game.player

    # try:
    result = game.ai_strike()
    player_board = game.player_map()
    # except Exception as exc:
    #     print(exc)
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=str(exc)
    #     )

    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    return _prepare_response(
        {
            'status': result,
            'player_board': player_board,
        }
    )

def _prepare_response(data: Dict[str, Any]) -> ORJSONResponse:
    return ORJSONResponse(
        {
            'data': data,
        }
    )