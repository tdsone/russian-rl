from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

Position = tuple[int, int]
Action = tuple[Position, Position]


@dataclass
class StepResult:
    state: Any
    reward: float
    done: bool
    info: dict


@dataclass
class Transition:
    state: Any
    action: Action
    reward: float
    next_state: Any
    done: bool


class Game(ABC):
    def __init__(self) -> None:
        self.state = None

    @abstractmethod
    def get_legal_actions(self) -> list[Action]:
        pass

    @abstractmethod
    def step(self, action: Action) -> StepResult:
        pass

    @abstractmethod
    def save_game(self):
        pass
