from abc import ABC, abstractmethod
from typing import Any
from ..game.base import Action, Game, Transition


class Agent(ABC):
    def __init__(self, player: Any = None) -> None:
        self.player = player

    @abstractmethod
    def process_experience(self, transition: Transition) -> None:
        pass

    @abstractmethod
    def select_action(self, game: Game) -> Action:
        pass
