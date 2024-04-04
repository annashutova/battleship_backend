from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette import status

from webapp.api.game.router import game_router
from webapp.utils.auth.jwt import jwt_auth, JwtTokenT

from webapp.game.core import Player, BattleShipGame
from webapp.game.board import Board
from webapp.game.square import Square

from webapp.cache.cache import redis_set


@game_router.post('/create_game')
async def create_game(
    access_token: JwtTokenT = Depends(jwt_auth.validate_token),
) -> ORJSONResponse:
    user_id = access_token['user_id']

    x = 10
    player_squares = [[Square(x=i, y=j) for j in range(x)] for i in range(x)]
    ai_squares = [[Square(x=i, y=j) for j in range(x)] for i in range(x)]
    player_weight = [[1 for _ in range(x)] for _ in range(x)]
    ai_weight = [[1 for _ in range(x)] for _ in range(x)]

    player_board = Board(x=x, y=x, board=player_squares, weight=player_weight)
    ai_board = Board(x=x, y=x, board=ai_squares, weight=ai_weight)

    player = Player(user_id=user_id, is_ai=False, board=player_board)
    ai = Player(is_ai=True, board=ai_board)

    game = BattleShipGame(player=player, ai=ai, turn=player)

    # setup ships for ai
    try:
        game.setup_random_ships(ai)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )

    await redis_set(BattleShipGame.__name__, user_id, game.model_dump())

    return ORJSONResponse(
        {
            'status': 'success',
        }
    )