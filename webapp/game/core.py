from typing import List, Tuple, Any
from itertools import cycle
from random import randint, choice

from game.board import Board
from game.square import SquareStatus
from game.ship import Ship
from game.exceptions import (ShipLengthError, SquareStrikedError, GameConditionError,
                             PlayerDoesNotExist, MaxShipReachedError, PlayerTurnError,
                             StartedOrFinishedError)


def is_sub(sub, main):
    return all(item in main for item in sub)


class Player:
    def __init__(self, is_ai: bool, board: Board, user_id: int = 0, auto_setup: bool = True):
        self.user_id = user_id
        self.is_ai = is_ai
        self.auto_ship_setup = auto_setup
        self.board = board


class BattleShipGame:
    SHIP_TYPES = (1, 1, 1, 1, 2, 2, 2, 3, 3, 4)

    def __init__(self, user_id: int, auto_setup: bool, x=9, y=9, max_ship_count=10):
        self.player = Player(False, Board(x, y, max_ship_count), user_id, auto_setup)
        self.ai = Player(True, Board(x, y, max_ship_count))
        self.x = x
        self.y = y
        self.max_ship_count = max_ship_count
        self.turn = self.player
        self._cycle = cycle((self.ai, self.player))
        self.started = False
        self.finished = False
        self.winner = None

    def _validate_player(self, user_id: int):
        user_ids = [p.user_id for p in self.players]
        if user_id not in user_ids:
            raise PlayerDoesNotExist("The given player is not in this game")

    def _validate_start(self):
        if self.started:
            raise GameConditionError("Game is started")

    def _validate_finish(self):
        if self.finished:
            raise GameConditionError("Game is finished")

    def get_setup_rules(self) -> Tuple[int]:
        return self.SHIP_TYPES

    def get_player(self, user_id: int):
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id == user_id))

    def get_opponent(self, user_id: int):
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id != user_id))

    @property
    def players(self):
        return self.player, self.ai

    @property
    def turn(self):
        return self._turn

    @turn.setter
    def turn(self, player):
        if player not in self.players:
            raise PlayerTurnError(
                "player should be one of game's players. use change_turn method instead")
        self._turn = player

    @property
    def winner(self):
        return self._winner

    @winner.setter
    def winner(self, player: Any):
        self._validate_finish()
        if player not in self.players and player is not None:
            raise PlayerDoesNotExist("Should be one of the game's player")
        self._winner = player

    def change_turn(self):
        self.turn = next(self._cycle)

    def setup_random_ships(self):
        """
        Creates n number of ships based on game's ship count.
        The ships are created randomly at players boards.
        Ships can be only created randomly once.
        """
        self._validate_finish()
        player_board, ai_board = self.player.board, self.ai.board
        if all(len(board.ships) == self.max_ship_count for board in (player_board, ai_board)):
            raise MaxShipReachedError
        self._create_random_ships(ai_board)

        if self.player.auto_ship_setup:
            self._create_random_ships(player_board)

    def _create_random_ships(self, *boards: Board):
        """Create ships with random positions for given boards.

        Even though ships positions will be random, 
        There will be equal number of ships with equal length 
        through the boards.
        """
        ship_lengths = self.SHIP_TYPES
        length = next(ship_lengths)
        for board in boards:
            board_cords = board.cords
            while len(board.ships) != self.max_ship_count:
                i, j = choice(board_cords)  # base random cord
                four_sides = []
                four_sides.append([(i+z, j) for z in range(length)])
                four_sides.append([(i-z, j) for z in range(length)])
                four_sides.append([(i, j+z) for z in range(length)])
                four_sides.append([(i, j-z) for z in range(length)])
                for cords in four_sides:
                    if is_sub(cords, board_cords):
                        board.create_ship(cords)
                        for cord in cords:
                            board_cords.remove(cord)
                        length = next(ship_lengths)
                        break

    def place_ship(self, coords: List[Tuple[int, int]]) -> None:
        """Places a ship on specific coordinates."""
        self._validate_finish()
        player_board = self.player.board

        if len(player_board.ships) == self.max_ship_count:
            raise MaxShipReachedError

        player_board.create_ship(coords)

    def get_ship(self, cord: Tuple[int, int], user_id: int) -> Ship:
        """Returns the ship associated with the given cordinate."""
        player = self.get_player(user_id)
        square = player.board.get_square(cord)
        return square.ship

    def get_ships(self, user_id: Any) -> List[Ship]:
        """Returns all the ships for a user"""
        player = self.get_player(user_id)
        ships = player.board.ships
        return ships

    def move_ship(self, ship: Ship, cords: List[Tuple[int, int]], user: Any):
        """Moves a ship to the given cordinates."""
        self._validate_start()
        self._validate_finish()
        if len(cords) != ship.length:
            raise ShipLengthError
        player = self.get_player(user)
        board = player.board
        new_sqs = board.get_squares(cords)
        ship.squares = new_sqs

    def strike(self, cord: Tuple[int, int]) -> int:
        """Strikes a given cord on board depending on whos turn it is. Return the state of strike.

        the turn doesn't change if it hits a ship square.
        Missed or hit squares cannot be targeted again.
        """
        player = self.turn
        self._validate_finish()
        if not self.started:
            raise GameConditionError("The game hasn't been started")
        if self.turn != player:
            raise PlayerTurnError("It's not your turn yet.")
        board = self.get_opponent(player.user_id).board  # get opponent
        square = board.get_square(cord)
        if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
            raise SquareStrikedError
        if square.state == SquareStatus.EMPTY:
            square.state = SquareStatus.MISSED
            self.change_turn()
            return SquareStatus.MISSED
        else:
            square.state = SquareStatus.HIT

            if square.ship.is_destroyed():
                square.ship.mark_destroyed()
                return SquareStatus.DESTROYED

            if board.is_finished():
                self.winner = self.turn

            return SquareStatus.HIT

    def ai_strike(self, map: List[List[int]]) -> Tuple[int, int]:
        pass

    def player_map(self, user: Any) -> List[List[int]]:
        """Returns a 2D array showing the player's board"""
        player = self.get_player(user)
        return [[square.state for square in sq_list] for sq_list in player.board.squares]

    def opponent_map(self, user: Any) -> List[List[int]]:
        """
        Returns a 2D array showing the player's hidden board.
        This is the map that should be shown to player's opponent.
        """
        opp = self.get_opponent(user)
        return [[self._hide_map(square) for square in sq_list] for sq_list in opp.board.squares]

    @staticmethod
    def _hide_map(square) -> int:
        if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
            return square.state
        return SquareStatus.UNKNOWN

    @classmethod
    def start_game(cls, user_id, auto_setup):
        game = cls(user_id, auto_setup)
        game.setup_ships() # remove, should be called manually
        return game

    def __str__(self):
        return f"Players: {self.players}, finished: {self.finished}"

    def __repr__(self):
        return f"finished: {self.finished} started: {self.finished} turn: {self.turn}"
