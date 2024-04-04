from fastapi import HTTPException, Depends
from starlette import status

from webapp.utils.auth.jwt import jwt_auth, JwtTokenT

from webapp.game.core import BattleShipGame
from webapp.cache.cache import redis_get


async def get_game_by_user(access_token: JwtTokenT = Depends(jwt_auth.validate_token)) -> BattleShipGame:
    user_id = access_token['user_id']

    game_data = await redis_get(BattleShipGame.__name__, user_id)

    if game_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Game for user with id={user_id} not found'
        )

    return BattleShipGame(**game_data)