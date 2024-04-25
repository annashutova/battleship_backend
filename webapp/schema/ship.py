from typing import List, Tuple

from pydantic import BaseModel


class PlaceShip(BaseModel):
    coords: List[Tuple[int, int]]


class _GetPlayerBoard(BaseModel):
    player_board: List[List[int]]


class GetPlayerBoardResponse(BaseModel):
    data: _GetPlayerBoard


class _GetAIBoard(BaseModel):
    ai_board: List[List[int]]


class GetAIBoardResponse(BaseModel):
    data: _GetAIBoard


class _CreateRandomShips(BaseModel):
    player_board: List[List[int]]
    ai_board: List[List[int]]


class CreateRandomShipsResponse(BaseModel):
    data: _CreateRandomShips


class _CreateShip(BaseModel):
    player_board: List[List[int]]


class CreateShipResponse(BaseModel):
    data: _CreateShip
