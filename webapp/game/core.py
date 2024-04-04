from typing import List, Tuple, Any, ClassVar
from random import choice, shuffle
from enum import Enum

from pydantic import BaseModel, Field, validator

from webapp.game.board import Board
from webapp.game.square import Square, SquareStatus
from webapp.game.ship import Ship
from webapp.game.exceptions import (
    SquareStrikedError,
    GameConditionError,
    PlayerDoesNotExist,
    MaxShipReachedError,
    PlayerTurnError,
    NotValidChoiceError
)


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
    def validate_turn(cls, value, values):
        if value.user_id not in (values['player'].user_id, values['ai'].user_id):
            raise PlayerTurnError("Player should be one of the game's players. Use change_turn method instead")
        return value

    @validator("winner", pre=True)
    def validate_winner(cls, value, values):
        if not value is None and value.user_id not in (values['player'].user_id, values['ai'].user_id):
            raise PlayerDoesNotExist("Should be one of the game's player")
        return value

    def get_setup_rules(self) -> List[int]:
        return self.SHIP_TYPES

    def get_player(self, user_id: int) -> Player:
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id == user_id))

    def get_opponent(self, user_id: int) -> Player:
        self._validate_player(user_id)
        return next((p for p in self.players if p.user_id != user_id))

    @property
    def players(self):
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
                four_sides: List[List[Tuple[int]]] = []
                four_sides.append([(i+z, j) for z in range(length)])
                four_sides.append([(i-z, j) for z in range(length)])
                four_sides.append([(i, j+z) for z in range(length)])
                four_sides.append([(i, j-z) for z in range(length)])
                shuffle(four_sides)
                for coords in four_sides:
                    if is_sub(coords, board_coords):
                        try:
                            board.create_ship(coords)
                        except Exception:
                            break
                        print('coords: ', coords)
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

    def get_ship(self, coord: Tuple[int, int], user_id: int) -> Ship:
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
        """Returns strike result of the ai."""
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
        """Strikes a given cord on board depending on whos turn it is. Return the state of strike.

        the turn doesn't change if it hits a ship square.
        Missed or hit squares cannot be targeted again.
        """
        square = board.get_square(coord)
        if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
            raise SquareStrikedError
        if square.state == SquareStatus.EMPTY:
            square.state = SquareStatus.MISSED
            self.change_turn()
            return HitStatus.MISS
        else:
            square.state = SquareStatus.HIT
            square.ship.hit_ship()
            print(f'after hit: {square.ship.hp}')

            if board.is_finished():
                self.winner = self.turn
            print(square.ship.is_destroyed())

            if square.ship.is_destroyed():
                board.mark_destroyed_ship(square.ship)
                return HitStatus.DESTROYED

            return HitStatus.HIT

    def player_map(self) -> List[List[int]]:
        """Returns a 2D array showing the player's board"""
        return [[square.state for square in sq_list] for sq_list in self.player.board.squares]

    def opponent_map(self, user_id: int) -> List[List[int]]:
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


def is_sub(sub, main):
    return all(item in main for item in sub)


# class BattleShipGame:
#     SHIP_TYPES = (1, 1, 1, 1, 2, 2, 2, 3, 3, 4)

#     def __init__(self, user_id: int, auto_setup: bool, x=9, y=9, max_ship_count=10):
#         self.player = Player(False, Board(x, y, max_ship_count), user_id, auto_setup)
#         self.ai = Player(True, Board(x, y, max_ship_count))
#         self.x = x
#         self.y = y
#         self.max_ship_count = max_ship_count
#         self.turn = self.player
#         self._cycle = cycle((self.ai, self.player))
#         self.started = False
#         self.finished = False
#         self.winner = None

#     def _validate_player(self, user_id: int):
#         user_ids = [p.user_id for p in self.players]
#         if user_id not in user_ids:
#             raise PlayerDoesNotExist("The given player is not in this game")

#     def _validate_start(self):
#         if self.started:
#             raise GameConditionError("Game is started")

#     def _validate_finish(self):
#         if self.finished:
#             raise GameConditionError("Game is finished")

#     def get_setup_rules(self) -> Tuple[int]:
#         return self.SHIP_TYPES

#     def get_player(self, user_id: int):
#         self._validate_player(user_id)
#         return next((p for p in self.players if p.user_id == user_id))

#     def get_opponent(self, user_id: int):
#         self._validate_player(user_id)
#         return next((p for p in self.players if p.user_id != user_id))

#     @property
#     def players(self):
#         return self.player, self.ai

#     @property
#     def turn(self):
#         return self._turn

#     @turn.setter
#     def turn(self, player):
#         if player not in self.players:
#             raise PlayerTurnError(
#                 "player should be one of game's players. use change_turn method instead")
#         self._turn = player

#     @property
#     def winner(self):
#         return self._winner

#     @winner.setter
#     def winner(self, player: Any):
#         self._validate_finish()
#         if player not in self.players and player is not None:
#             raise PlayerDoesNotExist("Should be one of the game's player")
#         self._winner = player

#     def change_turn(self) -> None:
#         if self.turn == self.player:
#             self.turn = self.ai
#         else:
#             self.turn = self.player

#     def setup_random_ships(self):
#         """
#         Creates n number of ships based on game's ship count.
#         The ships are created randomly at players boards.
#         Ships can be only created randomly once.
#         """
#         self._validate_finish()
#         player_board, ai_board = self.player.board, self.ai.board
#         if all(len(board.ships) == self.max_ship_count for board in (player_board, ai_board)):
#             raise MaxShipReachedError
#         self._create_random_ships(ai_board)

#         if self.player.auto_ship_setup:
#             self._create_random_ships(player_board)

#     def _create_random_ships(self, *boards: Board):
#         """Create ships with random positions for given boards.

#         Even though ships positions will be random, 
#         There will be equal number of ships with equal length 
#         through the boards.
#         """
#         ship_lengths = self.SHIP_TYPES
#         length = next(ship_lengths)
#         for board in boards:
#             board_cords = board.cords
#             while len(board.ships) != self.max_ship_count:
#                 i, j = choice(board_cords)  # base random cord
#                 four_sides = []
#                 four_sides.append([(i+z, j) for z in range(length)])
#                 four_sides.append([(i-z, j) for z in range(length)])
#                 four_sides.append([(i, j+z) for z in range(length)])
#                 four_sides.append([(i, j-z) for z in range(length)])
#                 for cords in four_sides:
#                     if is_sub(cords, board_cords):
#                         board.create_ship(cords)
#                         for cord in cords:
#                             board_cords.remove(cord)
#                         length = next(ship_lengths)
#                         break

#     def place_ship(self, coords: List[Tuple[int, int]]) -> None:
#         """Places a ship on specific coordinates."""
#         self._validate_finish()
#         player_board = self.player.board

#         if len(player_board.ships) == self.max_ship_count:
#             raise MaxShipReachedError

#         player_board.create_ship(coords)

#     def get_ship(self, cord: Tuple[int, int], user_id: int) -> Ship:
#         """Returns the ship associated with the given cordinate."""
#         player = self.get_player(user_id)
#         square = player.board.get_square(cord)
#         return square.ship

#     def get_ships(self, user_id: Any) -> List[Ship]:
#         """Returns all the ships for a user"""
#         player = self.get_player(user_id)
#         ships = player.board.ships
#         return ships

#     # def move_ship(self, ship: Ship, cords: List[Tuple[int, int]], user: Any):
#     #     """Moves a ship to the given cordinates."""
#     #     self._validate_start()
#     #     self._validate_finish()
#     #     if len(cords) != ship.length:
#     #         raise ShipLengthError
#     #     player = self.get_player(user)
#     #     board = player.board
#     #     new_sqs = board.get_squares(cords)
#     #     ship.squares = new_sqs

#     def make_strike(self, coord: Tuple[int, int], board: Board) -> str:
#         """Strikes a given cord on board depending on whos turn it is. Return the state of strike.

#         the turn doesn't change if it hits a ship square.
#         Missed or hit squares cannot be targeted again.
#         """
#         square = board.get_square(coord)
#         if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
#             raise SquareStrikedError
#         if square.state == SquareStatus.EMPTY:
#             square.state = SquareStatus.MISSED
#             self.change_turn()
#             return HitStatus.MISS
#         else:
#             square.state = SquareStatus.HIT

#             if square.ship.is_destroyed():
#                 square.ship.mark_destroyed()
#                 return HitStatus.DESTROYED

#             if board.is_finished():
#                 self.winner = self.turn

#             return HitStatus.HIT
    
#     def player_strike(self, coord: Tuple[int, int]) -> int:
#         """Returns strike result for the player."""
#         player = self.player
#         self._validate_finish()
#         if not self.started:
#             raise GameConditionError("The game hasn't been started")
#         if self.turn != player:
#             raise PlayerTurnError("It's not your turn yet.")
#         board = self.ai.board
        
#         return self.make_strike(coord, board)

#     def ai_strike(self) -> Tuple[int, int]:
#         """Returns strike result for the ai."""
#         ai = self.ai

#         self._validate_finish()
#         if not self.started:
#             raise GameConditionError("The game hasn't been started")

#         player_hidden_board = self.opponent_map(self.player.user_id)
#         player_board = self.player.board

#         ai_board = self.ai.board

#         ai_board.recalculate_weight_map(player_hidden_board)
#         coord = choice(ai_board.get_max_weight_coords())
        
#         return self.make_strike(coord, player_board)

#     def player_map(self, user: Any) -> List[List[int]]:
#         """Returns a 2D array showing the player's board"""
#         player = self.get_player(user)
#         return [[square.state for square in sq_list] for sq_list in player.board.squares]

#     def opponent_map(self, user_id: Any) -> List[List[int]]:
#         """
#         Returns a 2D array showing the player's hidden board.
#         This is the map that should be shown to player's opponent.
#         """
#         opp = self.get_opponent(user_id)
#         return [[self._hide_map(square) for square in sq_list] for sq_list in opp.board.squares]

#     @staticmethod
#     def _hide_map(square) -> int:
#         if square.state in [SquareStatus.MISSED, SquareStatus.HIT, SquareStatus.DESTROYED]:
#             return square.state
#         return SquareStatus.UNKNOWN

#     @classmethod
#     def start_game(cls, user_id, auto_setup):
#         game = cls(user_id, auto_setup)
#         game.setup_ships() # remove, should be called manually
#         return game

#     def __str__(self):
#         return f"Players: {self.players}, finished: {self.finished}"

#     def __repr__(self):
#         return f"finished: {self.finished} started: {self.finished} turn: {self.turn}"
