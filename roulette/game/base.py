from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class StepResult:
    state: Any
    reward: float
    done: bool
    info: dict


class Game(ABC):
    def __init__(self) -> None:
        self.state = None

    @abstractmethod
    def get_legal_actions(self) -> list:
        pass

    @abstractmethod
    def step(self, action) -> StepResult:
        pass

    @abstractmethod
    def save_game(self):
        pass
