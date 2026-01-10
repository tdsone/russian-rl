# russian-rl

Learning reinforcement learning for two Russian board/card games.

## Ugolki (Уголки / Corners)

### Setup
- 8×8 board
- White: 16 pieces in top-left 4×4 corner
- Black: 16 pieces in bottom-right 4×4 corner
- White moves first

### Goal
Move all your pieces to the opponent's starting corner.

### Legal Moves

**Step**: Move one square orthogonally (N/E/S/W) to an empty square.

**Jump**: Hop over exactly one piece (yours or opponent's) orthogonally to an empty square. Can chain multiple jumps in one turn but may stop at any point.

```
Step:           Jump:              Chain Jump:
W · □    →     W B □    →        W B □ B □
□ W □          □ □ W             □ □ □ □ W
```

### Restrictions
- No diagonal moves
- Cannot jump to occupied squares
- Chain jumps are optional (can stop early)

### Stalemate
- **Move limit**: Game ends in draw after 200 moves

---

## Design Decisions

- **Game interface**: Abstract base class (`ABC`) with `get_legal_actions()`, `step()`, `reset()`
- **Board representation**: `torch.Tensor` (8×8), values: `1` = white, `-1` = black, `0` = empty
- **RL loop**: Gymnasium-style interface (`state, reward, done, info = env.step(action)`)
- **Stalemate**: Move limit (200) — simple and prevents infinite loops during training
- **Actions**: Represented as `(from_pos, to_pos)` tuples (chain jumps = single action to final position)
