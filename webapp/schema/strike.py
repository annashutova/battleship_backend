from typing import List, Tuple

from pydantic import BaseModel


class StrikeCoord(BaseModel):
    coord: Tuple[int, int]


class _PlayerStrike(BaseModel):
    status: int
    ai_board: List[List[int]]
    finished: bool


class PlayerStrikeResponse(BaseModel):
    data: _PlayerStrike


class _AIStrike(BaseModel):
    status: int
    player_board: List[List[int]]
    finished: bool


class AIStrikeResponse(BaseModel):
    data: _AIStrike
