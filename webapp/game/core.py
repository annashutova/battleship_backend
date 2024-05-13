from enum import Enum
from random import choice, shuffle
from typing import Any, ClassVar, Dict, List, Tuple

from pydantic import BaseModel, Field, validator

from webapp.game.board import Board
from webapp.game.exceptions import (
    CordinatesValidationError,
    GameConditionError,
    MaxShipReachedError,
    PlayerDoesNotExist,
    PlayerTurnError,
    SquareStateError,
    SquareStrikedError,
)
from webapp.game.ship import Ship
from webapp.game.square import Square, SquareStatus


class HitStatus(Enum):
    HIT = 'hit'
    MISS = 'miss'
    DESTROYED = 'destroyed'


class Player(BaseModel):
    user_id: int = Field(default=0)
    is_ai: bool
    board: Board


class BattleShipGame(BaseModel):
    SHIP_TYPES: ClassVar[List[int]] = [1, 1, 1, 1, 2, 2, 2, 3, 3, 4]

    player: Player
    ai: Player
    max_ship_count: int = Field(default=10)
    turn: Player
    started: bool = Field(default=True)
    finished: bool = Field(default=False)
    winner: Player | None = Field(default=None)

    @validator("turn")
    @classmethod
    def validate_turn(cls, value: Any, values: Dict[str, Any]) -> Player:
        if value.user_id not in (values['player'].user_id, values['ai'].user_id):
            raise PlayerTurnError("Player should be one of the game's players. Use change_turn method instead")
        return value

    @validator("winner")
    @classmethod
    def validate_winner(cls, value: Any, values: Dict[str, Any]) -> Player | None:
        if value is not None and value.user_id not in (values['player'].user_id, values['ai'].user_id):
            raise PlayerDoesNotExist("Should be one of the game's player")
        return value

    def get_player(self, user_id: int) -> Player:
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id == user_id))

    def get_opponent(self, user_id: int) -> Player:
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id != user_id))

    @property
    def players(self) -> Tuple[Player, Player]:
        return self.player, self.ai

    def change_turn(self) -> None:
        if self.turn.user_id == self.player.user_id:
            self.turn = self.ai
        else:
            self.turn = self.player

    # передается ии и пользователь, если он выбрал рандомную расстановку, иначе только ии
    def setup_random_ships(self, player: Player) -> None:
        """
        Creates n number of ships based on game's ship count.
        The ships are created randomly at players boards.
        Ships can be only created randomly once.
        """
        self._validate_finish()
        board = player.board
        if len(board.ships) == self.max_ship_count:
            raise MaxShipReachedError
        self._create_random_ships(board)

    def _create_random_ships(self, board: Board) -> None:
        """Create ships with random positions for given board.

        Even though ships positions will be random,
        There will be equal number of ships with equal length
        through the boards.
        """
        board_coords = board.coords
        for length in self.SHIP_TYPES:
            retry = True
            while retry:
                i, j = choice(board_coords)  # base random cord
                four_sides = [
                    [(i + z, j) for z in range(length)],
                    [(i - z, j) for z in range(length)],
                    [(i, j + z) for z in range(length)],
                    [(i, j - z) for z in range(length)],
                ]
                shuffle(four_sides)
                for coords in four_sides:
                    # if is_sub(coords, board_coords):
                    try:
                        board.create_ship(coords)
                    except (CordinatesValidationError, SquareStateError):
                        break
                    print(f'ship coords: {coords}')
                    for coord in coords:
                        board_coords.remove(coord)
                    retry = False
                    break

    def place_ship(self, coords: List[Tuple[int, int]]) -> None:
        """Places a ship on specific coordinates."""
        self._validate_finish()
        player_board = self.player.board

        if len(player_board.ships) == self.max_ship_count:
            raise MaxShipReachedError

        player_board.create_ship(coords)

    def get_ship(self, coord: Tuple[int, int], user_id: int) -> Ship | None:
        """Returns the ship associated with the given cordinate."""
        player = self.get_player(user_id)
        square = player.board.get_square(coord)
        return square.ship

    def get_ships(self, user_id: Any) -> List[Ship]:
        """Returns all the ships for a user"""
        player = self.get_player(user_id)
        ships = player.board.ships
        return ships

    def player_strike(self, coord: Tuple[int, int]) -> HitStatus:
        """Returns strike result of the player."""
        player = self.player
        self._validate_finish()
        if not self.started:
            raise GameConditionError("The game hasn't been started")
        if self.turn.user_id != player.user_id:
            raise PlayerTurnError("It's not your turn yet.")
        ai_board = self.ai.board

        return self.make_strike(coord, ai_board)

    def ai_strike(self) -> HitStatus:
        """Returns strike result of the AI."""
        ai = self.ai

        self._validate_finish()
        if not self.started:
            raise GameConditionError("The game hasn't been started")

        player_hidden_board = self.opponent_map(ai.user_id)
        player_board = self.player.board

        ai_board = ai.board

        ai_board.recalculate_weight_map(player_hidden_board)
        coord = choice(ai_board.get_max_weight_coords())

        return self.make_strike(coord, player_board)

    def make_strike(self, coord: Tuple[int, int], board: Board) -> HitStatus:
        """Strikes a given cord on board depending on who's turn it is. Return the state of strike.

        The turn doesn't change if it hits a ship square.
        Missed or hit squares cannot be targeted again.
        """
        square = board.get_square(coord)
        if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
            raise SquareStrikedError
        if square.state == SquareStatus.EMPTY:
            square.state = SquareStatus.MISSED
            self.change_turn()
            return HitStatus.MISS
        square.state = SquareStatus.HIT
        if ship := square.ship:
            ship.hit_ship()

            if board.is_finished():
                self.finished = True
                self.winner = self.turn

            if ship.is_destroyed():
                board.mark_destroyed_ship(ship)
                return HitStatus.DESTROYED

        return HitStatus.HIT

    def player_map(self) -> List[List[SquareStatus]]:
        """Returns a 2D array showing the player's board"""
        return [[square.state for square in sq_list] for sq_list in self.player.board.squares]

    def opponent_map(self, user_id: int) -> list[list[SquareStatus]]:
        """
        Returns a 2D array showing the player's hidden board.
        This is the map that should be shown to player's opponent.
        """
        opp = self.get_opponent(user_id)
        return [[self._hide_map(square) for square in sq_list] for sq_list in opp.board.squares]

    @staticmethod
    def _hide_map(square: Square) -> SquareStatus:
        if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
            return square.state
        return SquareStatus.UNKNOWN

    def _validate_player(self, user_id: int) -> None:
        user_ids = [p.user_id for p in self.players]
        if user_id not in user_ids:
            raise PlayerDoesNotExist("The given player is not in this game")

    def _validate_start(self) -> None:
        if self.started:
            raise GameConditionError("Game is started")

    def _validate_finish(self) -> None:
        if self.finished:
            raise GameConditionError("Game is finished")


def is_sub(sub: List[Any], main: List[Any]) -> bool:
    return all(item in main for item in sub)
