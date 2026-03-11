"""Random agent that selects moves uniformly at random."""

import random

from roulette.agents.base import Agent
from roulette.game.base import Action, Game, Transition


class RandomAgent(Agent):
    """An agent that plays completely randomly."""

    def process_experience(self, transition: Transition) -> None:
        """Random agent doesn't learn from experience."""
        pass

    def select_action(self, game: Game) -> Action:
        """Select a random legal action."""
        actions = game.get_legal_actions()
        if not actions:
            raise ValueError("No legal actions available")
        return random.choice(actions)
