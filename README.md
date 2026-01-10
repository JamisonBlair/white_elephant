# Balancing the Elephant


This repository contains a Python simulation of a **White Elephant (a.k.a. Yankee Swap)** gift exchange game. The model captures realistic player behavior, gift quality variation, stealing rules, and several experimental rule variants.

The code is designed for **experimentation and analysis**, not UI or gameplay. It is especially suitable for:

* Studying fairness and advantage in turn order
* Exploring how gift quality distributions affect outcomes
* Comparing White Elephant rule variants
* Running Monte Carlo simulations

---

## Overview

At a high level, the simulation consists of:

* **Gifts** with intrinsic quality modifiers
* **Players** with heterogeneous preferences and risk thresholds
* A **turn-based game engine** that enforces White Elephant rules
* Optional **variants** such as early swap cards or extra turns

Each player acts greedily based on their private desirability scores, subject to a personal threshold that determines whether stealing is worth it.

---

## Core Concepts

### Gifts

Each gift:

* Has a unique ID
* Has a hidden quality modifier (possibly including rare "jackpots")
* Can only be stolen a limited number of times (`lock_num`)
* May temporarily or permanently lock against further steals

Gift quality influences how much players value the gift but is never directly observed by them.

---

### Players

Each player:

* Has a unique desirability score for *every* gift
* Holds exactly one gift by the end of the game
* Has a personal **stealing threshold**
* May hold a **swap card** (variant-dependent)

Players are not strategic planners. They act myopically:

> *"Is the best available gift better than what I’m willing to accept?"*

---

### Turn Mechanics

On a player’s turn:

1. All currently stealable gifts are identified
2. The most desirable available gift is selected
3. If its desirability exceeds the player’s threshold:

   * The gift is stolen
   * The robbed player immediately takes a turn
4. Otherwise:

   * The player unwraps a random remaining gift
   * The round advances

This recursion models the classic White Elephant steal chains.

---

## Game Variants

The simulation supports multiple rule variants via the `variant` parameter:

### `normal` (default)

* Standard White Elephant rules
* No swaps beyond normal steals

### `early_player_swaps`

* The first `swap_card_thresh` players receive a one-time swap card
* When a gift is unwrapped, eligible players may swap if:

  * They prefer the new gift
  * The desirability is close to their threshold

This models promotional or experimental rule sets.

### `p1_extra_turn`

* Player 1 receives an additional post-game swap opportunity
* Useful for testing first-player advantage

---

## Jackpot Gifts

When `jackpot=True`, gift quality is sampled from a distribution with:

* A small negative-to-neutral base range
* A low-probability, large positive bonus ("jackpot")

This creates rare, extremely valuable gifts that can dominate steal behavior.

---

## Code Structure

```
white_elephant/
│
├── Gift
│   └── Tracks quality, steals, and lock state
│
├── Player
│   └── Stores desirabilities, threshold, and swap ability
│
├── WhiteElephantGame
│   ├── Game initialization
│   ├── Turn execution
│   ├── Stealing and swapping logic
│   └── Variant handling
│
└── sample_gift_quality
    └── Gift quality sampling with optional jackpots
```

---

## Example Usage

```python
from white_elephant import WhiteElephantGame

game = WhiteElephantGame(
    n_players=10,
    seed=42,
    jackpot=True,
    variant="normal"
)

game.run()

# Inspect results
for player in game.players:
    print(player.id, player.gifts_held)
```

---

## Design Notes

* **Deterministic reproducibility** is supported via random seeds
* All player preferences are fixed at initialization
* No player has access to global game state or future information
* The model intentionally avoids dynamic re-evaluation of desirability

These constraints make the simulation suitable for statistical analysis and academic-style modeling.

---

## Analysis


### Normal play: number of steals a gift can have increases
![Rare jackpot gift dominating play](animations/normal__nplayers_15__nruns_5000__locknum_(1, 15).gif)

### Variant Comparison: Player 1 Swaps at the End
![Effect of early player swap cards](animations/p1_extra_turn__nplayers_15__nruns_5000__locknum_(1, 15).gif)

### Variant: Player Swaps
![Steal chains forming and resolving](animations/early_player_swaps__nplayers_15__nruns_10000__locknum_2_swapcardthresh_(1, 15).gif)

<!-- 
## Limitations

* No validation of impossible states (assumes correct usage)
* Recursion depth grows with long steal chains (should not be a problem with reasonable number of players and allowable stealing)
* Players only hold one gift in the current model
* No learning, memory, or strategic planning

---

## Suggested Extensions

* Multi-gift holding variants
* Explicit utility functions instead of thresholds
* Group-level fairness metrics
* Visualization of steal graphs
* Refactoring recursion into an explicit turn stack -->

---

## License

This code is provided for experimentation and analysis. No warranty is implied.

---

If you are using this model for research, simulation studies, or blog posts, consider documenting the variant parameters and random seeds for reproducibility.
