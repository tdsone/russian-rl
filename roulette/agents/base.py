from abc import ABC, abstractmethod


class Agent(ABC):
    @abstractmethod
    def process_experience(self):
        pass

    @abstractmethod
    def select_action(self):
        pass
