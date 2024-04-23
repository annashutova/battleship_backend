from typing import List, Tuple

from pydantic import BaseModel


class PlaceShip(BaseModel):
    coords: List[Tuple[int, int]]
