import random


def sample_gift_quality(
    base_range=(-0.5, 0.1),
    jackpot_prob=0.01,
    jackpot_range=(0.9, 1.0)
):
    """
    Sample a gift quality modifier with a small probability of a large
    positive "jackpot" boost.

    The base quality is drawn uniformly from `base_range`. With probability
    `jackpot_prob`, an additional bonus drawn from `jackpot_range` is added
    to the base value.

    Parameters
    ----------
    base_range : tuple of float, optional
        Lower and upper bounds for the base quality draw.
    jackpot_prob : float, optional
        Probability that a jackpot bonus is applied.
    jackpot_range : tuple of float, optional
        Lower and upper bounds for the jackpot bonus.

    Returns
    -------
    float
        The sampled quality modifier.
    """
    base = random.uniform(*base_range)

    if random.random() < jackpot_prob:
        jackpot = random.uniform(*jackpot_range)
        return base + jackpot

    return base


# -------------------
# Gift
# -------------------

class Gift:
    """
    Represents a single gift in the White Elephant game.

    Attributes
    ----------
    id : int
        Unique identifier for the gift.
    quality_modifier : float
        Intrinsic quality modifier influencing player desirability.
    steal_count : int
        Number of times the gift has been stolen.
    locked : bool
        Whether the gift is currently locked and cannot be stolen.
    last_stolen_turn : int or None
        Turn index on which the gift was last stolen.
    lock_num : int
        Maximum number of steals allowed before the gift becomes permanently locked.
    unwrapped : bool
        Whether the gift has been unwrapped.
    """

    def __init__(self, gift_id, quality_modifier, lock_num=2):
        """
        Initialize a gift.

        Parameters
        ----------
        gift_id : int
            Unique identifier for the gift.
        quality_modifier : float
            Base quality modifier for the gift.
        lock_num : int, optional
            Number of allowed steals before the gift locks permanently.
        """
        self.id = gift_id
        self.quality_modifier = quality_modifier
        self.steal_count = 0
        self.locked = False
        self.last_stolen_turn = None
        self.lock_num = lock_num
        self.unwrapped = False

    def can_be_stolen(self, current_turn):
        """
        Determine whether the gift can be stolen on the current turn.

        A gift cannot be stolen if it is locked or if it was stolen on the
        immediately preceding turn.

        Parameters
        ----------
        current_turn : int
            The current turn number.

        Returns
        -------
        bool
            True if the gift may be stolen, False otherwise.
        """
        if self.locked:
            return False
        if self.last_stolen_turn == current_turn - 1:
            return False
        return True

    def record_steal(self, current_turn):
        """
        Record a steal event for the gift and update lock status.

        Parameters
        ----------
        current_turn : int
            The turn on which the gift was stolen.
        """
        self.steal_count += 1
        self.last_stolen_turn = current_turn
        if self.steal_count >= self.lock_num:
            self.locked = True


# -------------------
# Player
# -------------------

class Player:
    """
    Represents a player in the White Elephant game.

    Attributes
    ----------
    id : int
        Unique identifier for the player.
    desirabilities : dict[int, float]
        Mapping from gift ID to desirability score.
    threshold : float
        Minimum desirability required for the player to steal a gift.
    gifts_held : list[int]
        List of gift IDs currently owned by the player.
    swap_card : bool
        Whether the player currently holds a swap card.
    """

    def __init__(self, player_id, desirabilities, threshold, swap_card=False):
        """
        Initialize a player.

        Parameters
        ----------
        player_id : int
            Unique identifier for the player.
        desirabilities : dict[int, float]
            Mapping from gift ID to desirability score.
        threshold : float
            Desirability threshold for stealing behavior.
        swap_card : bool, optional
            Whether the player starts with a swap card.
        """
        self.id = player_id
        self.desirabilities = desirabilities
        self.threshold = threshold
        self.gifts_held = []
        self.swap_card = swap_card

    def desirability(self, gift_id):
        """
        Return the player's desirability score for a given gift.

        Parameters
        ----------
        gift_id : int
            ID of the gift.

        Returns
        -------
        float
            Desirability score for the gift.
        """
        return self.desirabilities[gift_id]


# -------------------
# Game
# -------------------

class WhiteElephantGame:
    """
    Simulation of a White Elephant gift exchange game.

    This class manages players, gifts, turn-taking logic, stealing,
    swapping variants, and overall game progression.
    """

    def __init__(self, 
                 n_players, 
                 seed=None, 
                 jackpot=False, 
                 lock_num=2, 
                 variant='normal',
                 swap_card_thresh=3,
                 verbose=False
                ):
        """
        Initialize a White Elephant game instance.

        Parameters
        ----------
        n_players : int
            Number of players (and gifts) in the game.
        seed : int or None, optional
            Random seed for reproducibility.
        jackpot : bool, optional
            Whether to enable jackpot gift quality sampling.
        lock_num : int, optional
            Maximum number of steals before a gift locks.
        variant : str, optional
            Game variant controlling special rules. Options: ['p1_extra_turn','early_player_swaps']
        swap_card_thresh : int, optional
            Number of early players eligible for swap cards.
        verbose : bool, print more information about the game.
        """
        if seed is not None:
            random.seed(seed)

        self.n_players = n_players
        self.round = 0
        self.jackpot = jackpot
        self.lock_num = lock_num
        self.verbose = verbose
        self.variant = variant
        self.swap_card_thresh = swap_card_thresh
        
        if variant not in ['p1_extra_turn','early_player_swaps']:
            variant = 'normal'
            if self.verbose:
                print('variant not recognized, playing normal game.')

        # Create gifts
        self.gifts = {}
        for i in range(n_players):
            if self.jackpot is False:
                quality = random.uniform(-0.25, 0.25)
            else:
                quality = sample_gift_quality(base_range=(-0.25, 0.25))
            self.gifts[i] = Gift(i, quality, lock_num=self.lock_num)

        # Create players
        self.players = []
        for i in range(n_players):
            desirabilities = {}
            for g in self.gifts.values():
                base = random.uniform(0.2, 0.8)
                noise = random.uniform(-0.15, 0.15)
                desirabilities[g.id] = min(
                    0.97,
                    max(0.0, base + g.quality_modifier + noise)
                )

            threshold = random.uniform(0.7, 1.0)

            if self.variant == "early_player_swaps" and i < self.swap_card_thresh:
                swap_card = True
            else:
                swap_card = False

            self.players.append(
                Player(i, desirabilities, threshold, swap_card=swap_card)
            )

        self.wrapped_gifts = list(self.gifts.keys())
        self.ownership = {}  # gift_id -> player
        self.history = ''

    def take_turn(self, player):
        """
        Execute a single turn for a player.

        The player attempts to steal the most desirable available gift.
        If no acceptable gift is available, the player unwraps a new gift.
        Steals may trigger recursive turns by robbed players.

        Parameters
        ----------
        player : Player
            The active player.
        """
        gift_options = self.stealable_gifts(player)
        best_gift = self.best_available_gift(player, gift_options)

        if best_gift:
            robbed_player = self.steal_gift(player, best_gift)
            self.take_turn(robbed_player)
        else:
            self.unwrap_gift(player)
            self.round += 1

    def stealable_gifts(self, player):
        """
        Collect all gifts that the player may legally steal.

        Parameters
        ----------
        player : Player
            The player whose turn it is.

        Returns
        -------
        list[int]
            List of stealable gift IDs.
        """
        gifts_to_steal = []
        for other_player in self.players:
            if other_player != player:
                gifts_to_steal.extend(other_player.gifts_held)

        gifts_to_steal = list(
            filter(
                lambda x: (not self.gifts[x].locked)
                and (self.gifts[x].steal_count < self.lock_num),
                gifts_to_steal,
            )
        )

        self.unlock_gifts()
        return gifts_to_steal

    def unlock_gifts(self):
        """
        Unlock all gifts.

        This is used to reset temporary lock states between steal evaluations.
        """
        for gift in self.gifts.values():
            gift.locked = False

    def best_available_gift(self, player, gift_options):
        """
        Determine the best available gift for a player to steal.

        Parameters
        ----------
        player : Player
            The player making the decision.
        gift_options : list[int]
            Candidate gift IDs.

        Returns
        -------
        int or None
            ID of the chosen gift, or None if no gift meets the threshold.
        """
        if gift_options:
            best_gift = max(gift_options, key=lambda x: player.desirabilities[x])
        else:
            best_gift = None

        if best_gift:
            if player.desirabilities[best_gift] > player.threshold:
                return best_gift
            else:
                best_gift = None

        return best_gift

    def steal_gift(self, player, gift_id):
        """
        Transfer ownership of a gift via stealing.

        Parameters
        ----------
        player : Player
            The player stealing the gift.
        gift_id : int
            ID of the gift being stolen.

        Returns
        -------
        Player
            The player who was robbed.
        """
        robbed_player = self.ownership[gift_id]
        robbed_player.gifts_held.remove(gift_id)

        self.ownership[gift_id] = player
        player.gifts_held.append(gift_id)

        self.gifts[gift_id].locked = True
        self.gifts[gift_id].steal_count += 1

        return robbed_player

    def unwrap_gift(self, player):
        """
        Unwrap a random remaining gift and assign it to the player.

        Parameters
        ----------
        player : Player
            The player unwrapping the gift.
        """
        unwrapped_gift = random.choice(self.wrapped_gifts)
        self.wrapped_gifts.remove(unwrapped_gift)

        self.ownership[unwrapped_gift] = player
        player.gifts_held.append(unwrapped_gift)

        if self.variant == "early_player_swaps":
            swapper = self.swap_check(unwrapped_gift)
            if swapper:
                self.swap_gift(swapper, gift_to_swap=unwrapped_gift)

    def swap_gift(self, swapper, gift_to_swap='highest'):
        """
        Execute a gift swap involving a swap-card holder.

        Parameters
        ----------
        swapper : Player
            Player initiating the swap.
        gift_to_swap : int or str, optional
            Gift ID to swap, or 'highest' to auto-select the best option.
        """
        if gift_to_swap == 'highest':
            gift_to_swap = None
            gift_options = self.stealable_gifts(swapper)

            if gift_options:
                best_gift = max(gift_options, key=lambda x: swapper.desirabilities[x])
            else:
                best_gift = None

            if best_gift:
                if swapper.desirabilities[best_gift] > swapper.desirabilities[swapper.gifts_held[0]]:
                    gift_to_swap = best_gift

            if gift_to_swap:
                self.swap_gift(swapper, gift_to_swap=gift_to_swap)

        else:
            swappee = self.ownership[gift_to_swap]
            swappee.gifts_held.remove(gift_to_swap)

            self.ownership[gift_to_swap] = swapper
            worse_gift = swapper.gifts_held.pop()
            swapper.gifts_held.append(gift_to_swap)

            self.ownership[worse_gift] = swappee
            swappee.gifts_held.append(worse_gift)

            self.gifts[gift_to_swap].steal_count += 1

    def swap_check(self, gift_id):
        """
        Check whether any player with a swap card wants to swap for a gift.

        Parameters
        ----------
        gift_id : int
            ID of the newly unwrapped gift.

        Returns
        -------
        Player or None
            Player who executes the swap, if any.
        """
        players_with_swaps = list(
            filter(lambda x: x.swap_card and x.gifts_held != [], self.players)
        )
        #random.shuffle(players_with_swaps)

        for player in players_with_swaps:
            if (
                player.desirability(player.gifts_held[0]) < player.desirability(gift_id)
                and (player.threshold - 0.05) < player.desirability(gift_id)
            ):
                player.swap_card = False
                return player

    def run(self):
        """
        Run the full White Elephant game simulation.

        Executes one turn per player and applies any variant-specific
        post-round rules.
        """
        if self.history == 'done':
            print('Game complete. Look at results or start a new instance!')
            return

        for player in self.players:
            self.take_turn(player)

        if self.variant == 'p1_extra_turn':
            player_1 = self.players[0]
            self.swap_gift(player_1)

        self.history = 'done'
