import torch
import pytest

from games import Ugolki


class TestGetLegalActions:
    """Tests for Ugolki.get_legal_actions()"""

    def test_starting_position_white_has_16_moves(self):
        """At start, white has exactly 16 legal moves (edge pieces can step out)."""
        game = Ugolki.create_game()
        actions = game.get_legal_actions()

        assert len(actions) == 16

    def test_starting_position_includes_jumps_over_own_pieces(self):
        """At start, pieces can jump over adjacent own pieces."""
        game = Ugolki.create_game()
        actions = game.get_legal_actions()

        # Example: piece at (2,3) can jump over (3,3) to (4,3)
        assert ((2, 3), (4, 3)) in actions
        # Example: piece at (3,2) can jump over (3,3) to (3,4)
        assert ((3, 2), (3, 4)) in actions

    def test_simple_step_to_empty_square(self):
        """A piece can step to an adjacent empty square."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # Single white piece in center
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # Should be able to step in all 4 directions
        expected = {
            ((3, 3), (2, 3)),  # North
            ((3, 3), (4, 3)),  # South
            ((3, 3), (3, 2)),  # West
            ((3, 3), (3, 4)),  # East
        }
        assert set(actions) == expected

    def test_cannot_step_onto_occupied_square(self):
        """A piece cannot step onto an occupied square."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece
        board[3, 4] = -1  # Black piece blocking east
        board[4, 3] = 1  # White piece blocking south
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # (3,3) should not be able to step to (3,4) or (4,3)
        from_33 = [a for a in actions if a[0] == (3, 3)]
        destinations = {a[1] for a in from_33}

        assert (3, 4) not in destinations
        assert (4, 3) not in destinations

    def test_jump_over_piece(self):
        """A piece can jump over another piece to an empty square."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece
        board[3, 4] = -1  # Black piece to jump over
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # Should be able to jump to (3, 5)
        assert ((3, 3), (3, 5)) in actions

    def test_jump_over_own_piece(self):
        """A piece can jump over its own color."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece
        board[3, 4] = 1  # Another white piece to jump over
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # (3,3) should be able to jump to (3, 5)
        assert ((3, 3), (3, 5)) in actions

    def test_cannot_jump_to_occupied_square(self):
        """Cannot jump if landing square is occupied."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece
        board[3, 4] = -1  # Piece to jump over
        board[3, 5] = -1  # Landing blocked
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()
        from_33 = [a for a in actions if a[0] == (3, 3)]
        destinations = {a[1] for a in from_33}

        assert (3, 5) not in destinations

    def test_chain_jump(self):
        """A piece can chain multiple jumps."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[0, 0] = 1  # White piece
        board[0, 1] = -1  # First piece to jump
        board[0, 3] = -1  # Second piece to jump
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # Should reach (0,2) after first jump AND (0,4) after chain
        assert ((0, 0), (0, 2)) in actions
        assert ((0, 0), (0, 4)) in actions

    def test_chain_jump_with_turn(self):
        """Chain jumps can turn corners (L-shape)."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[0, 0] = 1  # White piece
        board[0, 1] = -1  # Jump right
        board[1, 2] = -1  # Then jump down
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # Should reach (0,2) then (2,2)
        assert ((0, 0), (0, 2)) in actions
        assert ((0, 0), (2, 2)) in actions

    def test_piece_at_corner_limited_moves(self):
        """A piece in the corner has limited directions."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[0, 0] = 1  # Corner piece
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()

        # Can only step south or east
        assert set(actions) == {((0, 0), (0, 1)), ((0, 0), (1, 0))}

    def test_black_turn(self):
        """When it's black's turn, only black pieces can move."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece
        board[5, 5] = -1  # Black piece
        game = Ugolki(board)
        game.turn = "black"

        actions = game.get_legal_actions()

        # All moves should be from the black piece position
        for (from_row, from_col), _ in actions:
            assert (from_row, from_col) == (5, 5)

    def test_no_diagonal_moves(self):
        """Diagonal moves are not allowed."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1  # White piece in center
        game = Ugolki(board)
        game.turn = "white"

        actions = game.get_legal_actions()
        destinations = {a[1] for a in actions}

        # Diagonal squares should not be reachable
        assert (2, 2) not in destinations
        assert (2, 4) not in destinations
        assert (4, 2) not in destinations
        assert (4, 4) not in destinations


class TestStepAndWinConditions:
    """Tests for Ugolki.step() and win conditions."""

    def test_step_returns_step_result(self):
        """Step should return a StepResult dataclass."""
        game = Ugolki.create_game()
        actions = game.get_legal_actions()
        result = game.step(actions[0])

        assert hasattr(result, "state")
        assert hasattr(result, "reward")
        assert hasattr(result, "done")
        assert hasattr(result, "info")

    def test_step_not_done_during_normal_play(self):
        """Game should not be done during normal play."""
        game = Ugolki.create_game()
        actions = game.get_legal_actions()
        result = game.step(actions[0])

        assert result.done is False
        assert result.reward == 0.0

    def test_white_wins_when_all_pieces_in_black_corner(self):
        """White wins when all 16 white pieces are in black's corner."""
        board = torch.zeros((8, 8), dtype=torch.long)
        # Place 15 white pieces in black's corner (rows 4-7, cols 4-7)
        board[4:, 4:] = 1
        board[7, 7] = 0  # Clear one spot for the winning move
        board[7, 3] = 1  # Place piece outside ready to move in
        game = Ugolki(board)
        game.turn = "white"

        # Move the piece into the corner to complete the win
        result = game.step(((7, 3), (7, 4)))

        # White should be one move away still, let's move to (7,7) via steps
        # Actually we need to move to 7,7 to win. Let's just verify the initial setup
        # creates a winning condition after the move lands in the corner area
        # For this test, let's just verify the winning scenario directly
        assert result.done is False  # Not a win yet - piece at (7,4) not (7,7)

        # Set up a proper winning scenario
        board2 = torch.zeros((8, 8), dtype=torch.long)
        board2[4:, 4:] = 1
        board2[4, 4] = 0  # Clear one spot
        board2[4, 3] = 1  # Piece ready to move in
        game2 = Ugolki(board2)
        game2.turn = "white"

        result2 = game2.step(((4, 3), (4, 4)))
        assert result2.done is True
        assert result2.info["winner"] == "white"

    def test_white_wins_reward_is_10(self):
        """White gets reward of 10 when winning."""
        board = torch.zeros((8, 8), dtype=torch.long)
        # Place 15 white pieces in black's corner
        board[4:, 4:] = 1
        board[4, 4] = 0  # Clear one spot for the winning move
        board[3, 4] = 1  # Place piece that will move in
        game = Ugolki(board)
        game.turn = "white"

        result = game.step(((3, 4), (4, 4)))

        assert result.done is True
        assert result.reward == 10.0
        assert result.info["winner"] == "white"

    def test_black_wins_when_all_pieces_in_white_corner(self):
        """Black wins when all 16 black pieces are in white's corner."""
        board = torch.zeros((8, 8), dtype=torch.long)
        # Place 15 black pieces in white's corner (rows 0-3, cols 0-3)
        board[:4, :4] = -1
        board[3, 3] = 0  # Clear one spot for the winning move
        board[4, 3] = -1  # Place piece that will move in
        game = Ugolki(board)
        game.turn = "black"

        result = game.step(((4, 3), (3, 3)))

        assert result.done is True
        assert result.reward == 10.0
        assert result.info["winner"] == "black"

    def test_no_winner_with_pieces_not_in_corner(self):
        """No winner if pieces are not all in opponent's corner."""
        game = Ugolki.create_game()
        winner = game._check_winner()
        assert winner is None

    def test_check_winner_white(self):
        """_check_winner returns 'white' when white has won."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[4:, 4:] = 1  # All 16 white pieces in black's corner
        game = Ugolki(board)

        assert game._check_winner() == "white"

    def test_check_winner_black(self):
        """_check_winner returns 'black' when black has won."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[:4, :4] = -1  # All 16 black pieces in white's corner
        game = Ugolki(board)

        assert game._check_winner() == "black"

    def test_turn_switches_after_step(self):
        """Turn should switch from white to black after a step."""
        game = Ugolki.create_game()
        assert game.turn == "white"

        actions = game.get_legal_actions()
        game.step(actions[0])

        assert game.turn == "black"

    def test_step_updates_board_state(self):
        """Step should update the board state correctly."""
        board = torch.zeros((8, 8), dtype=torch.long)
        board[3, 3] = 1
        game = Ugolki(board)
        game.turn = "white"

        result = game.step(((3, 3), (3, 4)))

        assert result.state[3, 3].item() == 0
        assert result.state[3, 4].item() == 1
