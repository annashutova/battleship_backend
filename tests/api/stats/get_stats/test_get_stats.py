from datetime import datetime
from pathlib import Path

import pytest
from freezegun import freeze_time
from httpx import AsyncClient
from starlette import status

from tests.const import URLS

BASE_DIR = Path(__file__).parent
FIXTURES_PATH = BASE_DIR / 'fixtures'


@pytest.mark.parametrize(
    (
        'username',
        'period',
        'wins',
        'losses',
        'ships_sank',
        'ships_destroyed',
        'expected_status',
        'fixtures',
    ),
    [
        (
            1234567,
            1,
            1,
            1,
            12,
            17,
            status.HTTP_200_OK,
            [
                FIXTURES_PATH / 'sirius.user.json',
                FIXTURES_PATH / 'sirius.game.json',
            ],
        ),
        (
            1234567,
            7,
            2,
            1,
            14,
            27,
            status.HTTP_200_OK,
            [
                FIXTURES_PATH / 'sirius.user.json',
                FIXTURES_PATH / 'sirius.game.json',
            ],
        ),
        (
            1234567,
            30,
            3,
            1,
            18,
            37,
            status.HTTP_200_OK,
            [
                FIXTURES_PATH / 'sirius.user.json',
                FIXTURES_PATH / 'sirius.game.json',
            ],
        ),
    ],
)
@pytest.mark.asyncio()
@pytest.mark.usefixtures('_common_api_fixture')
async def test_get_stats(
    client: AsyncClient,
    username: int,
    period: int,
    wins: int,
    losses: int,
    ships_sank: int,
    ships_destroyed: int,
    expected_status: int,
    access_token: str,
    db_session: None,
) -> None:
    with freeze_time(datetime(2024, 4, 16, 15, 0, 0)):
        response = await client.get(
            URLS['stats']['get_stats'],
            params={'period': period},
            headers={'Authorization': f'Bearer {access_token}'},
        )

    assert response.status_code == expected_status

    response_data = response.json().get('data')
    assert response_data.get('wins') == wins
    assert response_data.get('losses') == losses
    assert response_data.get('ships_sank') == ships_sank
    assert response_data.get('ships_destroyed') == ships_destroyed
