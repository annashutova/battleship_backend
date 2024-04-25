from typing import List

from pydantic import BaseModel


class _SetupRules(BaseModel):
    ship_types: List[int]


class CreatGameResponse(BaseModel):
    status: str


class SetupRulesResponse(BaseModel):
    data: _SetupRules
