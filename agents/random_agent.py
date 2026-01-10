"""Random agent that selects moves uniformly at random."""

import random

from agents.base import Agent
from games.base import Game


class RandomAgent(Agent):
    """An agent that plays completely randomly."""

    def process_experience(self):
        """Random agent doesn't learn from experience."""
        pass

    def select_action(self, game: Game) -> tuple[tuple[int, int], tuple[int, int]]:
        """Select a random legal action."""
        actions = game.get_legal_actions()
        if not actions:
            raise ValueError("No legal actions available")
        return random.choice(actions)
