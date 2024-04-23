from fastapi import Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.api.login.router import auth_router
from webapp.crud.user import create_user, get_user
from webapp.db.postgres import get_session
from webapp.schema.user import UserInfo, UserLoginResponse
from webapp.utils.auth.jwt import jwt_auth


@auth_router.post(
    '/login',
    response_model=UserLoginResponse,
)
async def login(
    body: UserInfo,
    session: AsyncSession = Depends(get_session),
) -> ORJSONResponse:
    user = await get_user(session, body)

    if user is None:
        user = await create_user(session, body)

    return ORJSONResponse(
        {
            'access_token': jwt_auth.create_token(user.id),
        }
    )
