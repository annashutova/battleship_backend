from typing import List, Tuple

from game.square import Square, SquareStatus
from game.ship import Ship
from game.exceptions import (
    CordinatesValidationError,
    MaxShipReachedError,
    SquaresNotAttachedError,
    SquareStateError,
)


class Board:

    def __init__(self, x: int, y: int, max_ship_count: int):
        """For handling squares and ships instances in BattleShipGame class.

        y is an indicator that defines how long each array is,
        while x defines how many arrays should be in board.
        The number of ships on the board cannot exceed max ship count attribute.
        """
        self._board = [[Square(i, j) for j in range(y)] for i in range(x)]
        self._weight = [[1 for _ in range(y)] for _ in range(x)]
        self._ships = []
        self.max_ship_count = max_ship_count

    @property
    def squares(self):
        return self._board

    @property
    def x(self):
        return len(self._board)

    @property
    def y(self):
        return len(self._board[0])

    @property
    def ships(self):
        return self._ships

    @property
    def cords(self):
        return [square.cord for sq_list in self._board for square in sq_list]

    def _validate_cordinates(self, *cords):
        for cord in cords:
            i, j = cord[0], cord[1]
            if not 0 <= i <= self.x-1 or not 0 <= j <= self.y-1:
                raise CordinatesValidationError()

    def get_square(self, cord: Tuple[int, int]) -> Square:
        self._validate_cordinates(cord)
        return self._board[cord[0]][cord[1]]

    def get_squares(self, cordinates: List[Tuple[int, int]] = None) -> List[Square]:
        return [self.get_square(cord) for cord in cordinates]

    def update_state(self, state: int, cord: Tuple[int, int]) -> None:
        square = self.get_square(cord)
        square.state = state

    def create_ship(self, cordinates: List[Tuple[int, int]]) -> Ship:
        """Creates a ship at given coordinates.
    
        Given squares should be attached and not occupied.
        """
        if len(self._ships) >= self.max_ship_count:
            raise MaxShipReachedError
        self._validate_cordinates(cordinates)
        self._validate_continuous_coords(cordinates)
        self._validate_empty_surrounding(cordinates)
        square_objects = self.get_squares(cordinates)
        ship = Ship(square_objects)
        self._ships.append(ship)
        return ship
    
    def _validate_empty_surrounding(self, coordinates: List[Tuple[int, int]]) -> None: # возможно можно оптимизировать
        for coord in coordinates:
            for x in range(coord[0] - 1, coord[0] - 2):
                if not 0 <= x <= self.x - 1:
                    continue
                for y in range(coord[1] - 1, coord[1] - 2):
                    if not 0 <= y <= self.y - 1:
                        continue
                    square = self.get_square((x, y))
                    if square.state != 0:
                        raise SquareStateError(
                            "The surrounding squares are not in empty state"
                        )
    
    def _validate_continuous_coords(self, coordinates: List[Tuple[int, int]]) -> None:
        x_sorted_coords = sorted(coordinates, key=lambda coord: coord[0])
        y_sorted_coords = sorted(coordinates, key=lambda coord: coord[1])

        for sorted_coords in [x_sorted_coords, y_sorted_coords]:
            for i in range(1, len(sorted_coords)):
                if (
                    sorted_coords[i][0] - sorted_coords[i - 1][0] != 1
                    and sorted_coords[i][1] - sorted_coords[i - 1][1] != 1
                ):
                    raise SquaresNotAttachedError
    
    # функция возвращает список координат с самым большим коэффициентом шанса попадания
    def get_max_weight_coords(self) -> List[Tuple[int, int]]:
        weights = []
        max_weight = -1

        for x in range(self.x):
            for y in range(self.y):
                if self._weight[x][y] > max_weight:
                    weights = [(x, y)]
                    max_weight = self._weight[x][y]
                elif self._weight[x][y] == max_weight:
                    weights.append((x, y))

        return weights[max_weight]

    # пересчет веса клеток
    def recalculate_weight_map(self, opponent_map):
        # Для начала мы выставляем всем клеткам 1.
        # нам не обязательно знать какой вес был у клетки в предыдущий раз:
        # эффект веса не накапливается от хода к ходу.
        self._weight = [[1 for _ in range(self.y)] for _ in range(self.x)]

        # Пробегаем по всем полю.
        # Если находим раненый корабль - ставим клеткам выше ниже и по бокам
        # коэффициенты умноженые на 50 т.к. логично что корабль имеет продолжение в одну из сторон.
        # По диагоналям от раненой клетки ничего не может быть - туда вписываем нули
        for x in range(self.x):
            for y in range(self.y):
                if opponent_map[x][y] == SquareStatus.HIT:
                    self._weight[x][y] = 0

                    if x - 1 >= 0:
                        if y - 1 >= 0:
                            self._weight[x - 1][y - 1] = 0
                        self._weight[x - 1][y] *= 50
                        if y + 1 < self.y:
                            self._weight[x - 1][y + 1] = 0

                    if x + 1 < self.x:
                        if y - 1 >= 0:
                            self._weight[x + 1][y - 1] = 0
                        self._weight[x + 1][y] *= 50
                        if y + 1 < self.y:
                            self._weight[x + 1][y + 1] = 0

                    if y - 1 >= 0:
                        self._weight[x][y - 1] *= 50
                    if y + 1 < self.y:
                        self._weight[x][y + 1] *= 50

                elif opponent_map[x][y] == SquareStatus.DESTROYED:
                    self._weight[x][y] = 0

                    if x - 1 >= 0:
                        if y - 1 >= 0:
                            self._weight[x - 1][y - 1] = 0
                        self._weight[x - 1][y] = 0
                        if y + 1 < self.y:
                            self._weight[x - 1][y + 1] = 0

                    if x + 1 < self.x:
                        if y - 1 >= 0:
                            self._weight[x + 1][y - 1] = 0
                        self._weight[x + 1][y] = 0
                        if y + 1 < self.y:
                            self._weight[x + 1][y + 1] = 0

                    if y - 1 >= 0:
                        self._weight[x][y - 1] = 0
                    if y + 1 < self.y:
                        self._weight[x][y + 1] = 0

                elif opponent_map[x][y] == SquareStatus.MISSED:
                    self._weight[x][y] = 0

    def is_finished(self) -> bool:
        for ship in self.ships:
            if not ship.is_destroyed():
                return False
        return True

    def __str__(self):
        string = '\n'
        for line in self._board:
            for square in line:
                string += square.__str__() + ' '
            string += '\n'
        return string
