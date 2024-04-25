from pydantic import BaseModel


class _GetStats(BaseModel):
    wins: int
    losses: int
    ships_sank: int
    ships_destroyed: int


class GetStatsResponse(BaseModel):
    data: _GetStats


class SaveDataResponse(BaseModel):
    status: str
