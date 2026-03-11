from abc import ABC, abstractmethod
from ..game.base import Action, Game, Transition


class Agent(ABC):
    @abstractmethod
    def process_experience(self, transition: Transition) -> None:
        pass

    @abstractmethod
    def select_action(self, game: Game) -> Action:
        pass
