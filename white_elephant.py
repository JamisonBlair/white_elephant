import random

def sample_gift_quality(
    base_range=(-0.5, 0.1),
    jackpot_prob=0.01,
    jackpot_range=(0.9, 1.0)
):
    base = random.uniform(*base_range)

    if random.random() < jackpot_prob:
        jackpot = random.uniform(*jackpot_range)
        return base + jackpot

    return base


# -------------------
# Gift
# -------------------

class Gift:
    def __init__(self, gift_id, quality_modifier, lock_num=2):
        self.id = gift_id
        self.quality_modifier = quality_modifier
        self.steal_count = 0
        self.locked = False
        self.last_stolen_turn = None
        self.lock_num = lock_num
        self.unwrapped = False

    def can_be_stolen(self, current_turn):
        if self.locked:
            return False
        if self.last_stolen_turn == current_turn - 1:
            return False
        return True

    def record_steal(self, current_turn):
        self.steal_count += 1
        self.last_stolen_turn = current_turn
        if self.steal_count >= self.lock_num:
            self.locked = True


# -------------------
# Player
# -------------------

class Player:
    def __init__(self, player_id, desirabilities, threshold):
        self.id = player_id
        self.desirabilities = desirabilities  # gift_id -> desirability
        self.threshold = threshold
        self.gifts_held = []

    def desirability(self, gift_id):
        return self.desirabilities[gift_id]


# -------------------
# Game
# -------------------

class WhiteElephantGame:
    
    def __init__(self, 
                 n_players, 
                 seed=None, 
                 jackpot=False, 
                 lock_num=2, 
                 variant='normal',
                ):
        if seed is not None:
            random.seed(seed)

        self.n_players = n_players
        self.round = 0
        self.jackpot = jackpot
        self.lock_num = lock_num
        self.variant = variant

        # Create gifts
        self.gifts = {}
        for i in range(n_players):
            if self.jackpot == False:
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
                    .97,
                    max(0.0, base + g.quality_modifier + noise)
                )
            threshold = random.uniform(0.7, 1.0)
            self.players.append(Player(i, desirabilities, threshold))

        self.wrapped_gifts = list(self.gifts.keys())
        self.ownership = {}  # gift_id -> player_id
        self.history = []


    def take_turn(self, player):
        """
        1. Collect stealable items
        2. Find most desirable stealable item
        3. If none, then unwrap and end round.
        4. Else, steal item and have other player take turn
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

        gifts_to_steal = []
        for other_player in self.players:
            if other_player != player:
                gifts_to_steal.extend(other_player.gifts_held)

        gifts_to_steal = list(filter(lambda x: (not self.gifts[x].locked) 
                                     and (self.gifts[x].steal_count < self.lock_num)
                                     , gifts_to_steal
                                    )
                             )
        self.unlock_gifts()

        return gifts_to_steal

    def unlock_gifts(self):
        for gift in self.gifts.values():
            gift.locked = False

    def best_available_gift(self, player, gift_options):
        
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
        
        robbed_player = self.ownership[gift_id]
        robbed_player.gifts_held.remove(gift_id)

        self.ownership[gift_id] = player
        player.gifts_held.append(gift_id)

        self.gifts[gift_id].locked = True
        self.gifts[gift_id].steal_count += 1

        return robbed_player

    def unwrap_gift(self, player):

        unwrapped_gift = random.choice(self.wrapped_gifts)
        self.wrapped_gifts.remove(unwrapped_gift)
        self.ownership[unwrapped_gift] = player
        player.gifts_held.append(unwrapped_gift)

    def swap_gift(self, swapper, gift_to_swap='highest'):

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

    def run(self):

        for player in self.players:
            self.take_turn(player)

        if self.variant == 'p1_extra_turn':
            player_1 = self.players[0]
            self.swap_gift(player_1)
        