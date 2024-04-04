from enum import Enum
from pydantic import BaseModel, Field, validator

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
    x: int
    y: int
    state: SquareStatus = Field(default=SquareStatus.EMPTY)
    ship: Ship | None = Field(default=None)

    @validator("state")
    def validate_state(cls, value):
        if value not in SquareStatus:
            raise NotValidChoiceError("Invalid SquareStatus value")
        return value
    
    @property
    def cord(self):
        return (self.x, self.y)
    
    def place_ship(self, ship: Ship) -> None:
        self.ship = ship
        self.state = SquareStatus.SHIP


# class Square:
#     def __init__(self, x, y, state=SquareStatus.EMPTY):
#         self.state = state
#         self.x = x
#         self.y = y
#         self.ship = None

#     @property
#     def state(self):
#         return self._state

#     @state.setter
#     def state(self, value):
#         SquareStatus.validate(value)
#         self._state = value

#     @property
#     def cord(self):
#         return (self.x, self.y)

#     def __str__(self):
#         return SquareStatus(self.state).name  # 'eg. "EMPTY"'

#     def __repr__(self):
#         return f"({self.x}, {self.y}), STATE: {SquareStatus(self.state).name}"