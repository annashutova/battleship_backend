from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from webapp.api.game.router import game_router
from webapp.api.login.router import auth_router
from webapp.api.stats.router import stats_router
from webapp.middleware.logger import LogServerMiddleware
from webapp.middleware.metrics import MetricsMiddleware, metrics
from webapp.on_startup.logger import setup_logger
from webapp.on_startup.redis import start_redis


def setup_middleware(app: FastAPI) -> None:
    app.add_middleware(
        LogServerMiddleware,
    )

    # CORS Middleware should be the last.
    app.add_middleware(
        CORSMiddleware, allow_origins=['*'], allow_credentials=True, allow_methods=['*'], allow_headers=['*']
    )
    app.add_middleware(MetricsMiddleware)


def setup_routers(app: FastAPI) -> None:
    app.add_route('/metrics', metrics)

    routers = [
        auth_router,
        game_router,
        stats_router,
    ]

    for router in routers:
        app.include_router(router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    setup_logger()
    await start_redis()
    print('START APP')
    yield
    print('STOP APP')


def create_app() -> FastAPI:
    app = FastAPI(docs_url='/swagger', lifespan=lifespan)

    setup_middleware(app)
    setup_routers(app)

    return app
