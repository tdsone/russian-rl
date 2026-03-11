from dataclasses import dataclass, field

from roulette.agents.base import Agent
from roulette.game.base import Game, Transition


@dataclass
class EpisodeResult:
    steps: int
    winner: str | None
    transitions: dict[str, list[Transition]] = field(default_factory=dict)


class Runner:
    def __init__(self, game: Game, agents: dict) -> None:
        """
        Args:
            game: The game environment.
            agents: Mapping of player identity to Agent, e.g. {Player.WHITE: white_agent, Player.BLACK: black_agent}.
        """
        self.game = game
        self.agents = agents

    def run_episode(self, collect_transitions: bool = False) -> EpisodeResult:
        """Run one full episode, routing transitions to each agent.

        Args:
            collect_transitions: If True, also return all transitions in EpisodeResult.
        """
        self.game.reset()

        transitions: dict = {player: [] for player in self.agents}
        steps = 0
        result = None

        while True:
            player = self.game.current_player
            agent = self.agents[player]

            state = self.game.board.clone()
            action = agent.select_action(self.game)
            result = self.game.step(action)

            transition = Transition(
                state=state,
                action=action,
                reward=result.reward,
                next_state=result.state.clone(),
                done=result.done,
            )
            agent.process_experience(transition)

            if collect_transitions:
                transitions[player].append(transition)

            steps += 1

            if result.done:
                break

        winner = result.info.get("winner") if result else None
        return EpisodeResult(
            steps=steps,
            winner=winner,
            transitions=transitions if collect_transitions else {},
        )
