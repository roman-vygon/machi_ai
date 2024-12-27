from copy import deepcopy
from functools import reduce
from constants import player_limit
import numpy as np
from numpy.random import choice as rchoice

from Building import Building
from EstablishmentCount import EstablishmentCount
from constants import BUILDING_VECTOR_TEMPLATE
from player_ai import PlayerAI

use_max_probability = True

# this makes the probabilities slightly less deterministic
# modulate_prob = True
prob_mod = 0.


def choose_from_probs(probs, constraint_mask=None):
    # will almost always make optimal decision;
    if use_max_probability:
        if constraint_mask:
            probs = probs * constraint_mask
        if prob_mod:
            # np.maximum just in case modulation value is changed or some weird act of rngsus
            probs = probs * np.maximum(0, np.random.normal(1, prob_mod, len(probs)))
        probs = probs * (probs == np.max(probs)) + (probs ** 2 * 0.01 + 0.001) / len(probs)
        if constraint_mask:
            probs = probs * constraint_mask

    else:
        probs = probs ** 2 + 0.05 / len(
            probs)  # will select best option most likely, but can choose other ones with decent probability
        if constraint_mask:
            probs = probs * constraint_mask

    probs = probs / np.sum(probs)
    choice = rchoice(range(len(probs)), size=1, p=probs)
    return choice[0]


class Player:
    id: int
    coins: int
    buildings: dict[Building, int]
    # major_establishments: dict[str, bool]
    # landmarks: dict[str, bool]
    # establishments: dict[str, EstablishmentCount]
    is_first_turn: bool = True
    AI: PlayerAI

    def __init__(self):
        super().__init__()
        self.AI = PlayerAI(self)

    def serialize_data(self):
        """this vectorizes the number of buildings in each category a player has;
        only the number of coins is represented as an integer"""
        building_vector = deepcopy(BUILDING_VECTOR_TEMPLATE)
        for building in Building:
            vector = [0] * player_limit[building]
            for i in range(self.buildings[building]):
                vector[i] = 1
        for i, building in enumerate(BUILDING_ORDER):
            building_vector[i][self.buildings[building]] = 1
        flat_vector = [x for sub in building_vector for x in sub]
        flat_vector.append(self.coins)
        return flat_vector

    def complete_serialize(self):
        """this returns the complete and sufficient game state based on the player whose turn it is"""
        return reduce(list.__add__, [self.get_next_player(offset).serialize_data() for offset in range(4)])


class Player(object):
    """
    Represents a player in the game, managing their state, actions, and AI behavior.
    """

    def __init__(self, game, order, name=''):
        """
        Initializes a Player instance.

        Args:
            game: The game instance the player is part of.
            order: The player's turn order in the game.
            name: Optional; the model name or identifier for the player.
        """
        # Don't do this in production code; modifies global behavior of probability functions
        global use_max_probability
        global prob_mod
        use_max_probability = game.use_max_probability
        prob_mod = game.prob_mod
        self.game = game
        self.buildings = deepcopy(starting_buildings)
        self.coins = 0
        self.order = order
        self.shared_ai = False
        self.name = name
        self.id = order  # Unique identifier for the player
        self.win = 0
        self.extra_turn = False
        self.double = False
        # History tracking
        self.dice_history = []
        self.dice_history_turn = []
        self.dice_history_win = []
        self.buy_history = []
        self.buy_history_turn = []
        self.buy_history_win = []
        self.steal_history = []
        self.steal_history_turn = []
        self.steal_history_win = []
        self.swap_history = []
        self.swap_history_turn = []
        self.swap_history_win = []
        self.reroll_history = []
        self.reroll_history_turn = []
        self.reroll_history_win = []
        # AI
        self.AI = PlayerAI(self)

    def initialize_ai(self):
        """
        Initializes the player's AI, preparing it for decision-making.
        """
        self.AI.initialize_ai()

    def roll_dice(self):
        """
        Rolls dice for the player's turn and calculates the roll value.
        Sets the `double` attribute if a double is rolled with two dice.
        """
        dice = [randint(1, 6) for _ in range(self.roll)]
        if self.roll == 2 and dice[0] == dice[1]:
            self.double = True
        else:
            self.double = False
        self.roll_value = sum(dice)
        if self.game.record_game:
            self.game.game_record_file.write(
                f'ROLL: player {self.order} rolls a {self.roll_value} {str(dice)} with {self.roll} dice\n'
            )

    def update_win_history(self):
        """
        Updates the win history for all recorded player actions.
        """
        self.dice_history_win += [self.win] * (len(self.dice_history) - len(self.dice_history_win))
        self.buy_history_win += [self.win] * (len(self.buy_history) - len(self.buy_history_win))
        self.swap_history_win += [self.win] * (len(self.swap_history) - len(self.swap_history_win))
        self.steal_history_win += [self.win] * (len(self.steal_history) - len(self.steal_history_win))
        self.reroll_history_win += [self.win] * (len(self.reroll_history) - len(self.reroll_history_win))

    def reset_game(self, game, order):
        """
        Resets the player's state for a new game.

        Args:
            game: The new game instance.
            order: The player's new turn order.

        Returns:
            The reset Player instance.
        """
        self.game = game
        self.AI.game = game
        self.buildings = deepcopy(starting_buildings)
        self.coins = 3
        self.order = order
        self.win = 0
        return self

    def train_ai(self, reset=False):
        """
        Trains the player's AI and optionally resets action history.

        Args:
            reset: Boolean indicating whether to reset the player's action history.
        """
        if not self.shared_ai:
            self.AI.train()
        elif self.id == self.AI.shared.player_id:
            self.AI.train()
        if reset:
            self.flush_history(flush_shared=False)

    def flush_history(self, flush_shared=True):
        """
        Clears the player's action history to save memory or remove irrelevant data.

        Args:
            flush_shared: Whether to also flush the shared AI's history.
        """
        self.dice_history.clear()
        self.dice_history_turn.clear()
        self.buy_history.clear()
        self.buy_history_turn.clear()
        self.steal_history.clear()
        self.steal_history_turn.clear()
        self.swap_history.clear()
        self.swap_history_turn.clear()
        self.reroll_history.clear()
        self.reroll_history_turn.clear()
        self.dice_history_win.clear()
        self.buy_history_win.clear()
        self.steal_history_win.clear()
        self.swap_history_win.clear()
        self.reroll_history_win.clear()
        if self.shared_ai and flush_shared:
            self.AI.shared.flush_history()

    def get_next_player(self, offset=1):
        """
        Gets the next player in turn order, offset by the specified number of players.

        Args:
            offset: The number of players to skip.

        Returns:
            The next Player instance in turn order.
        """
        return self.game.get_next_player(self, offset)

    def decide_dice(self):
        if self.buildings['station'] == 0:
            self.roll = 1
            return 0
        probs = self.AI.eval_dice()
        choice = choose_from_probs(probs)
        if choice == 0:
            roll = 2
        else:
            roll = 1
        self.roll = roll
        self.AI.record_dice()
        return 0

    def decide_reroll(self):
        # note that you must reroll the same number of dice you originally rolled
        # yes, this is from the creators
        if self.buildings['radio_tower'] == 0:
            self.reroll = 0
            return 0
        self.prev_roll_value = self.roll_value
        probs = self.AI.eval_reroll()
        choice = choose_from_probs(probs)
        if choice == 0:
            self.reroll = 1
        else:
            self.reroll = 0
        if self.reroll == 1 and self.game.record_game:
            self.game.game_record_file.write("REROLL: player %d is rerolling!\n" % self.order)
        self.AI.record_reroll()
        return 0

    def decide_steal(self):
        """
        returns the offset of the player from whombst coin should be stolen
        """
        probs = self.AI.eval_steal()
        choice = choose_from_probs(probs)
        self.victim = self.get_next_player(choice + 1)
        # index is used for self.AI.record_steal()
        self.victim_index = choice + 1

    def decide_swap(self):
        self.create_swap_mask()
        probs = self.AI.eval_swap()
        self.swap_choice = choice = choose_from_probs(probs, constraint_mask=self.swap_mask)
        self.swap_opponent_offset = 1 + (choice // 144)
        self.swap_opponent_building = ((choice % 144) // 12)
        self.swap_self_building = (choice % 12)
        self.AI.record_swap()

    def decide_buy(self):
        self.create_buy_mask()
        probs = self.AI.eval_buy()
        self.buy_choice = choose_from_probs(probs, constraint_mask=self.buy_mask)
        self.AI.record_buy()
    def take_turn(self):
        """
        Executes the player's turn, including rolling dice, performing actions, and deciding purchases.
        """
        self.double = False
        self.decide_dice()
        self.roll_dice()
        self.decide_reroll()
        if self.reroll:
            self.roll_dice()
        self.game.activate_red(self)
        self.coins += self.calculate_green()
        self.game.activate_blue(self)
        self.calculate_purple()
        if self.game.record_game:
            self.game.game_record_file.write(f'COINS: player {self.order} has {self.coins} coins\n')
        self.decide_buy()
        if self.buy_choice != 19:
            self.buildings[BUILDING_ORDER[self.buy_choice]] += 1
            self.game.building_supply[BUILDING_ORDER[self.buy_choice]] -= 1
            self.coins -= building_cost[BUILDING_ORDER[self.buy_choice]]
            if self.game.record_game:
                self.game.game_record_file.write(
                    f'BUY: player {self.order} bought a(n) {BUILDING_ORDER[self.buy_choice]} (now has {self.buildings[BUILDING_ORDER[self.buy_choice]]})\n'
                )
        elif self.game.record_game:
            self.game.game_record_file.write(f'BUY: player {self.order} chooses not to buy anything\n')
        if self.double and self.buildings.amusement_park == 1:
            self.extra_turn = True
            if self.game.record_game:
                self.game.game_record_file.write(f'EXTRA TURN: player {self.order} gets an extra turn!\n')
        self.check_if_win()
