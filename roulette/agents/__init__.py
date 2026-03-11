from roulette.agents.base import Agent
from roulette.agents.random_agent import RandomAgent
from roulette.agents.naive_maxscore import NaiveScoreMaxAgent

AGENT_REGISTRY: dict[str, dict] = {
    "random": {
        "name": "Random",
        "difficulty": "Easy",
        "description": "Picks moves completely at random",
        "factory": RandomAgent,
    },
    "naive_maxscore": {
        "name": "Greedy",
        "difficulty": "Medium",
        "description": "Always picks the move with the best immediate progress",
        "factory": NaiveScoreMaxAgent,
    },
}

__all__ = ["Agent", "AGENT_REGISTRY", "NaiveScoreMaxAgent", "RandomAgent"]
