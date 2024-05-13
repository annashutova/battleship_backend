from typing import List, Tuple

from pydantic import BaseModel, Field

from webapp.game.exceptions import (
    CordinatesValidationError,
    MaxShipReachedError,
    SquaresNotAttachedError,
    SquareStateError,
)
from webapp.game.ship import Ship
from webapp.game.square import Square, SquareStatus


class Board(BaseModel):
    lines_cnt: int
    rows_cnt: int
    board: List[List[Square]]
    weight: List[List[int]]
    ships: List[Ship] = Field(default_factory=list)
    max_ship_count: int = Field(default=10)

    @property
    def squares(self) -> List[List[Square]]:
        return self.board

    @property
    def coords(self) -> List[Tuple[int, int]]:
        return [square.cord for squares in self.board for square in squares]

    def get_square(self, coord: Tuple[int, int]) -> Square:
        self._validate_coordinate(coord)
        return self.board[coord[0]][coord[1]]

    def get_squares(self, coordinates: List[Tuple[int, int]]) -> List[Square]:
        return [self.get_square(coord) for coord in coordinates]

    def create_ship(self, coordinates: List[Tuple[int, int]]) -> Ship:
        """Creates a ship at given coordinates.

        Given squares should be attached and not occupied.
        """
        if len(self.ships) >= self.max_ship_count:
            raise MaxShipReachedError
        self._validate_coordinates(coordinates)
        if len(coordinates) > 1:
            self._validate_continuous_coords(coordinates)
        self._validate_empty_surrounding(coordinates)
        squares = self.get_squares(coordinates)
        ship = Ship(coords=coordinates, hp=len(coordinates))

        for square in squares:
            square.place_ship(ship)

        self.ships.append(ship)
        return ship

    # функция возвращает список координат с самым большим коэффициентом шанса попадания
    def get_max_weight_coords(self) -> List[Tuple[int, int]]:
        weights = []
        max_weight = -1

        for x in range(self.lines_cnt):
            for y in range(self.rows_cnt):
                if self.weight[x][y] > max_weight:
                    weights = [(x, y)]
                    max_weight = self.weight[x][y]
                elif self.weight[x][y] == max_weight:
                    weights.append((x, y))

        return weights

    # пересчет веса клеток
    def recalculate_weight_map(self, opponent_map: list[list[SquareStatus]]) -> None:
        # Для начала мы выставляем всем клеткам 1.
        # нам не обязательно знать какой вес был у клетки в предыдущий раз:
        # эффект веса не накапливается от хода к ходу.
        self.weight = [[1 for _ in range(self.rows_cnt)] for _ in range(self.lines_cnt)]

        # Пробегаем по всем полю.
        # Если находим раненый корабль - ставим клеткам выше ниже и по бокам
        # коэффициенты умноженые на 50 т.к. логично что корабль имеет продолжение в одну из сторон.
        # По диагоналям от раненой клетки ничего не может быть - туда вписываем нули
        for x in range(self.lines_cnt):
            for y in range(self.rows_cnt):
                if opponent_map[x][y] == SquareStatus.HIT:
                    self.weight[x][y] = 0

                    if x - 1 >= 0:
                        if y - 1 >= 0:
                            self.weight[x - 1][y - 1] = 0
                        self.weight[x - 1][y] *= 50
                        if y + 1 < self.rows_cnt:
                            self.weight[x - 1][y + 1] = 0

                    if x + 1 < self.lines_cnt:
                        if y - 1 >= 0:
                            self.weight[x + 1][y - 1] = 0
                        self.weight[x + 1][y] *= 50
                        if y + 1 < self.rows_cnt:
                            self.weight[x + 1][y + 1] = 0

                    if y - 1 >= 0:
                        self.weight[x][y - 1] *= 50
                    if y + 1 < self.rows_cnt:
                        self.weight[x][y + 1] *= 50

                elif opponent_map[x][y] == SquareStatus.DESTROYED:
                    self.weight[x][y] = 0

                    if x - 1 >= 0:
                        if y - 1 >= 0:
                            self.weight[x - 1][y - 1] = 0
                        self.weight[x - 1][y] = 0
                        if y + 1 < self.rows_cnt:
                            self.weight[x - 1][y + 1] = 0

                    if x + 1 < self.lines_cnt:
                        if y - 1 >= 0:
                            self.weight[x + 1][y - 1] = 0
                        self.weight[x + 1][y] = 0
                        if y + 1 < self.rows_cnt:
                            self.weight[x + 1][y + 1] = 0

                    if y - 1 >= 0:
                        self.weight[x][y - 1] = 0
                    if y + 1 < self.rows_cnt:
                        self.weight[x][y + 1] = 0

                elif opponent_map[x][y] == SquareStatus.MISSED:
                    self.weight[x][y] = 0

    def mark_destroyed_ship(self, ship: Ship) -> None:
        squares = self.get_squares(ship.coords)
        for square in squares:
            square.state = SquareStatus.DESTROYED

    def is_finished(self) -> bool:
        return all(ship.is_destroyed() for ship in self.ships)

    def _validate_coordinates(self, coords: List[Tuple[int, int]]) -> None:
        for coord in coords:
            self._validate_coordinate(coord)

    def _validate_coordinate(self, coord: Tuple[int, int]) -> None:
        i, j = coord
        if not 0 <= i <= self.lines_cnt - 1 or not 0 <= j <= self.rows_cnt - 1:
            raise CordinatesValidationError()

    def _validate_empty_surrounding(self, coordinates: List[Tuple[int, int]]) -> None:
        for coord in coordinates:
            for x in range(coord[0] - 1, coord[0] + 2):
                if not 0 <= x <= self.lines_cnt - 1:
                    continue
                for y in range(coord[1] - 1, coord[1] + 2):
                    if not 0 <= y <= self.rows_cnt - 1:
                        continue
                    square = self.get_square((x, y))
                    if square.state != SquareStatus.EMPTY:
                        raise SquareStateError("The surrounding squares are not in empty state")

    @staticmethod
    def _validate_continuous_coords(coordinates: List[Tuple[int, int]]) -> None:
        is_parallel_x = all(coord[0] == coordinates[0][0] for coord in coordinates)
        is_parallel_y = all(coord[1] == coordinates[0][1] for coord in coordinates)

        if not (is_parallel_x or is_parallel_y):
            raise SquaresNotAttachedError

        if is_parallel_x:
            sorted_coords = sorted(coordinates, key=lambda x: x[1])
            for i in range(len(sorted_coords) - 1):
                if sorted_coords[i + 1][1] - sorted_coords[i][1] != 1:
                    raise SquaresNotAttachedError
        else:
            sorted_coords = sorted(coordinates, key=lambda x: x[0])
            for i in range(len(sorted_coords) - 1):
                if sorted_coords[i + 1][0] - sorted_coords[i][0] != 1:
                    raise SquaresNotAttachedError
