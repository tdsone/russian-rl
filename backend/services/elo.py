"""ELO rating calculation service.

Standard chess ELO formula:
- K-factor: 32 (standard for most players)
- Expected score: 1 / (1 + 10^((opponent_elo - player_elo) / 400))
- New ELO = old_elo + K * (actual_score - expected_score)
"""

K_FACTOR = 32


def calculate_expected_score(player_elo: float, opponent_elo: float) -> float:
    """Calculate expected score for a player against an opponent."""
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))


def calculate_elo_change(
    player_elo: float, opponent_elo: float, won: bool
) -> tuple[float, float]:
    """
    Calculate new ELO ratings for both players after a game.

    Args:
        player_elo: Current ELO of the player
        opponent_elo: Current ELO of the opponent
        won: True if player won, False if player lost

    Returns:
        Tuple of (new_player_elo, new_opponent_elo)
    """
    player_expected = calculate_expected_score(player_elo, opponent_elo)
    opponent_expected = calculate_expected_score(opponent_elo, player_elo)

    # Actual scores: 1 for win, 0 for loss
    player_actual = 1.0 if won else 0.0
    opponent_actual = 0.0 if won else 1.0

    new_player_elo = player_elo + K_FACTOR * (player_actual - player_expected)
    new_opponent_elo = opponent_elo + K_FACTOR * (opponent_actual - opponent_expected)

    return new_player_elo, new_opponent_elo
