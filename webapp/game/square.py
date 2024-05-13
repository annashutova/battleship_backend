from enum import Enum
from typing import Any, Tuple

from pydantic import BaseModel, Field, field_serializer, validator

from webapp.game.exceptions import NotValidChoiceError
from webapp.game.ship import Ship


class SquareStatus(Enum):
    EMPTY = 0
    MISSED = 1
    SHIP = 2
    HIT = 3
    UNKNOWN = 4
    DESTROYED = 5


class Square(BaseModel):
    x_coord: int
    y_coord: int
    state: SquareStatus = Field(default=SquareStatus.EMPTY)
    ship: Ship | None = Field(default=None)

    @field_serializer('ship')
    def serialize_ship(self, ship: Ship | None, _info: Any) -> None:
        return None

    @validator("state")
    def validate_state(cls, value: Any) -> int:
        if value not in SquareStatus:
            raise NotValidChoiceError(message="Invalid SquareStatus value")
        return value

    @property
    def cord(self) -> Tuple[int, int]:
        return self.x_coord, self.y_coord

    def place_ship(self, ship: Ship) -> None:
        self.ship = ship
        self.state = SquareStatus.SHIP
