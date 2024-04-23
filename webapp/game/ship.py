from typing import Any, Dict, List, Tuple

from pydantic import BaseModel, validator

from webapp.game.exceptions import ShipHPError


class Ship(BaseModel):
    coords: List[Tuple[int, int]]
    hp: int

    @validator("hp")
    def validate_hp(cls, value: Any, values: Dict[str, Any]) -> int:
        coords = values.get("coords")
        if coords is not None and (value < 0 or value > len(coords)):
            raise ShipHPError("Ship hp cannot be below 0 and above its length.")
        return value

    @property
    def length(self) -> int:
        return len(self.coords)

    def is_destroyed(self) -> bool:
        return self.hp == 0

    def hit_ship(self) -> None:
        if self.hp == 0:
            raise ShipHPError("Ship already has 0 hit points.")
        self.hp -= 1
