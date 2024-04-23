from typing import Any, Dict

from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette import status

from webapp.api.game.router import game_router
from webapp.cache.cache import redis_set
from webapp.cache.get_game import get_game_by_user
from webapp.game.core import BattleShipGame
from webapp.schema.ship import PlaceShip


@game_router.post('/setup_rules')
async def get_setup_rules(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    return _prepare_response(
        {
            'ship_types': game.SHIP_TYPES,
        }
    )


@game_router.post('/create_random_ships')
async def place_random_ships(
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player = game.player

    try:
        game.setup_random_ships(player)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    player_board = game.player_map()
    ai_board = game.opponent_map(player.user_id)

    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    return _prepare_response(
        {
            'player_board': player_board,
            'ai_board': ai_board,
        }
    )


@game_router.post('/create_ship')
async def place_ship(
    body: PlaceShip,
    game: BattleShipGame = Depends(get_game_by_user),
) -> ORJSONResponse:
    player = game.player

    try:
        game.place_ship(body.coords)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await redis_set(BattleShipGame.__name__, player.user_id, game.model_dump())

    return _prepare_response(
        {
            'player_board': game.player_map(),
        }
    )


def _prepare_response(data: Dict[str, Any]) -> ORJSONResponse:
    return ORJSONResponse(
        {
            'data': data,
        }
    )
