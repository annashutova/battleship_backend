from typing import Tuple

from pydantic import BaseModel


class StrikeCoord(BaseModel):
    coord: Tuple[int, int]
