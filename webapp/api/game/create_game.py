from fastapi import Depends, HTTPException
from fastapi.responses import ORJSONResponse
from starlette import status

from webapp.api.game.config import CELLS_COUNT
from webapp.api.game.router import game_router
from webapp.cache.cache import redis_set
from webapp.game.board import Board
from webapp.game.core import BattleShipGame, Player
from webapp.game.square import Square
from webapp.schema.game import CreatGameResponse
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth


@game_router.post(
    '/create_game',
    response_model=CreatGameResponse,
)
async def create_game(
    access_token: JwtTokenT = Depends(jwt_auth.validate_token),
) -> ORJSONResponse:
    user_id = access_token['user_id']

    player_squares = [[Square(x_coord=i, y_coord=j) for j in range(CELLS_COUNT)] for i in range(CELLS_COUNT)]
    ai_squares = [[Square(x_coord=i, y_coord=j) for j in range(CELLS_COUNT)] for i in range(CELLS_COUNT)]
    player_weight = [[1 for _ in range(CELLS_COUNT)] for _ in range(CELLS_COUNT)]
    ai_weight = [[1 for _ in range(CELLS_COUNT)] for _ in range(CELLS_COUNT)]

    player_board = Board(lines_cnt=CELLS_COUNT, rows_cnt=CELLS_COUNT, board=player_squares, weight=player_weight)
    ai_board = Board(lines_cnt=CELLS_COUNT, rows_cnt=CELLS_COUNT, board=ai_squares, weight=ai_weight)

    player = Player(user_id=user_id, is_ai=False, board=player_board)
    ai = Player(is_ai=True, board=ai_board)

    game = BattleShipGame(player=player, ai=ai, turn=player)

    # setup ships for AI
    try:
        game.setup_random_ships(ai)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await redis_set(BattleShipGame.__name__, user_id, game.model_dump())

    return ORJSONResponse(
        {
            'status': 'success',
        }
    )
