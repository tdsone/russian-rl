"""Random agent that maximises the action with the most progress in a given step"""

from roulette.agents import Agent
from roulette.game.base import Action, Game, Transition
from roulette.game.ugolki import Player


class NaiveScoreMaxAgent(Agent):
    """Greedy agent that always picks the move with the highest immediate score delta."""

    def process_experience(self, transition: Transition) -> None:
        pass

    def compute_best_action(self, game, actions: list[Action]) -> Action:
        best_action = None
        best_score = -100

        for action in actions:
            (from_row, from_col), (to_row, to_col) = action
            delta = (to_row - from_row), (to_col - from_col)

            score = 0
            if game.turn == Player.WHITE:
                score = sum(delta)
            if game.turn == Player.BLACK:
                score = -sum(delta)

            if not best_action:
                best_action = action
                best_score = score
            elif score > best_score:
                best_action = action
                best_score = score

        return best_action

    def select_action(self, game: Game) -> Action:
        """Select a random legal action."""
        actions = game.get_legal_actions()
        if not actions:
            raise ValueError("No legal actions available")

        max_action = self.compute_best_action(game, actions)

        return max_action
