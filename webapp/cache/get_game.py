from fastapi import Depends, HTTPException
from starlette import status

from webapp.cache.cache import redis_get
from webapp.game.core import BattleShipGame
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth


async def get_game_by_user(access_token: JwtTokenT = Depends(jwt_auth.validate_token)) -> BattleShipGame:
    user_id = access_token['user_id']

    game_data = await redis_get(BattleShipGame.__name__, user_id)

    if game_data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Game for user with id={user_id} not found')

    game = BattleShipGame(**game_data)

    # put ships on boards
    for player in (game.ai, game.player):
        player_board = player.board.board
        for ship in player.board.ships:
            for coord in ship.coords:
                x_coord, y_coord = coord
                player_board[x_coord][y_coord].ship = ship

    return game
