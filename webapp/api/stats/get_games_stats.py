from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import Depends
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from webapp.api.stats.router import stats_router
from webapp.crud.stats import get_statistics
from webapp.db.postgres import get_session
from webapp.utils.auth.jwt import JwtTokenT, jwt_auth


@stats_router.get('/get_stats')
async def get_stats(
    period: int = 1,
    session: AsyncSession = Depends(get_session),
    access_token: JwtTokenT = Depends(jwt_auth.validate_token),
) -> ORJSONResponse:
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period)

    result = await get_statistics(session, start_date, end_date, access_token['user_id'])

    if result is not None:
        return _prepare_response(
            {
                'wins': result[0],
                'losses': result[1],
                'ships_sank': result[2],
                'ships_destroyed': result[3],
            }
        )
    else:
        return _prepare_response(
            {
                'wins': 0,
                'losses': 0,
                'ships_sank': 0,
                'ships_destroyed': 0,
            }
        )


def _prepare_response(data: Dict[str, Any]) -> ORJSONResponse:
    return ORJSONResponse(
        {
            'data': data,
        }
    )
