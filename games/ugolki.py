import random
import torch

from games.base import Game, StepResult

# Directions: North, East, South, West
DIRECTIONS = [(-1, 0), (0, 1), (1, 0), (0, -1)]


class Ugolki(Game):
    def __init__(self, board: torch.Tensor) -> None:
        super().__init__()
        self.board = board
        self.score_white = 0
        self.score_black = 0
        self.turn = "white"  # white starts

    def update_score(self):
        raise NotImplementedError

    def print_board(self) -> None:
        """Print the current board state to terminal."""
        symbols = {0: "·", 1: "W", -1: "B"}

        print("    " + "   ".join(str(i) for i in range(8)))
        print("  +" + "---+" * 8)

        for row in range(8):
            row_str = " | ".join(
                symbols[int(self.board[row, col].item())] for col in range(8)
            )
            print(f"{row} | {row_str} |")
            print("  +" + "---+" * 8)

        print(f"\nTurn: {self.turn}")

    @classmethod
    def create_game(cls):
        """Create a new game at starting position."""
        board = torch.zeros((8, 8), dtype=torch.long)
        # set white pieces as 1
        board[:4, :4] = 1
        # set black pieces as -1
        board[4:, 4:] = -1

        return cls(board)

    @classmethod
    def create_random_game(cls, num_moves: int | None = None):
        """
        Create a game at a random position by playing random moves.

        Args:
            num_moves: Number of random moves to play. If None, picks random 0-50.
        """
        game = cls.create_game()

        if num_moves is None:
            num_moves = random.randint(0, 50)

        for _ in range(num_moves):
            actions = game.get_legal_actions()
            if not actions:
                break
            action = random.choice(actions)
            game.apply_action(action)

        return game

    def apply_action(self, action: tuple[tuple[int, int], tuple[int, int]]) -> None:
        """Apply an action to the board (no validation, no return)."""
        (from_row, from_col), (to_row, to_col) = action
        # Move piece
        self.board[to_row, to_col] = self.board[from_row, from_col]
        self.board[from_row, from_col] = 0
        # Switch turn
        self.turn = "black" if self.turn == "white" else "white"

    def get_legal_actions(self) -> list[tuple[tuple[int, int], tuple[int, int]]]:
        """
        Returns list of (from_pos, to_pos) tuples for all legal moves.

        Legal actions:
        - move by one to a free adjacent field
        - jump 1 to n times over another piece if the field is free (only NESW not diagonal)
        """
        actions = []
        piece_value = 1 if self.turn == "white" else -1

        # Find all pieces of current player
        piece_positions = torch.where(self.board == piece_value)
        pieces = list(zip(piece_positions[0].tolist(), piece_positions[1].tolist()))

        for row, col in pieces:
            # 1. Simple steps (move by one)
            for dr, dc in DIRECTIONS:
                new_row, new_col = row + dr, col + dc
                if (
                    self._is_valid(new_row, new_col)
                    and self.board[new_row, new_col] == 0
                ):
                    actions.append(((row, col), (new_row, new_col)))

            # 2. Jumps (BFS to find all reachable via chain jumps)
            jump_destinations = self._get_jump_destinations(row, col)
            for dest in jump_destinations:
                actions.append(((row, col), dest))

        return actions

    def _is_valid(self, row: int, col: int) -> bool:
        """Check if position is within board bounds."""
        return 0 <= row < 8 and 0 <= col < 8

    def _get_jump_destinations(
        self, start_row: int, start_col: int
    ) -> set[tuple[int, int]]:
        """BFS to find all positions reachable via chain jumps."""
        reachable = set()
        visited = {(start_row, start_col)}  # Don't revisit starting position
        queue = [(start_row, start_col)]

        while queue:
            row, col = queue.pop(0)

            for dr, dc in DIRECTIONS:
                # Position of piece to jump over
                mid_row, mid_col = row + dr, col + dc
                # Landing position (2 squares away)
                land_row, land_col = row + 2 * dr, col + 2 * dc

                if (
                    self._is_valid(land_row, land_col)
                    and self._is_valid(mid_row, mid_col)
                    and self.board[mid_row, mid_col] != 0  # Must jump over a piece
                    and self.board[land_row, land_col] == 0  # Landing must be empty
                    and (land_row, land_col) not in visited
                ):
                    visited.add((land_row, land_col))
                    reachable.add((land_row, land_col))
                    queue.append((land_row, land_col))  # Continue chain from here

        return reachable

    def _check_winner(self) -> str | None:
        """
        Check if a player has won.

        Win condition: All 16 pieces in opponent's corner.
        - White wins if all 16 white pieces are in black's corner (rows 4-7, cols 4-7)
        - Black wins if all 16 black pieces are in white's corner (rows 0-3, cols 0-3)

        Returns:
            "white" if white wins, "black" if black wins, None if no winner yet.
        """
        # Check if white won: all white pieces (1) must be in rows 4-7, cols 4-7
        white_in_black_corner = (self.board[4:, 4:] == 1).sum().item()
        if white_in_black_corner == 16:
            return "white"

        # Check if black won: all black pieces (-1) must be in rows 0-3, cols 0-3
        black_in_white_corner = (self.board[:4, :4] == -1).sum().item()
        if black_in_white_corner == 16:
            return "black"

        return None

    def step(self, action: tuple[tuple[int, int], tuple[int, int]]) -> StepResult:
        """
        Apply action and return (state, reward, done, info).

        Returns:
            state: Current board tensor
            reward: 10.0 for win, -10.0 for loss, 0.0 otherwise
            done: True if game is over
            info: Dict with extra info (includes 'winner' if game is done)
        """
        # Track who made the move (before turn switches)
        moving_player = self.turn

        self.apply_action(action)

        # Check win conditions
        winner = self._check_winner()
        done = winner is not None
        info = {}

        if done:
            info["winner"] = winner
            # Reward from perspective of the player who just moved
            if winner == moving_player:
                reward = 10.0
            else:
                reward = -10.0
        else:
            reward = 0.0

        return StepResult(state=self.board, reward=reward, done=done, info=info)

    def save_game(self):
        # TODO implement this
        return
