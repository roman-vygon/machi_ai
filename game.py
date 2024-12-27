import csv
import math
import os
import random
from copy import deepcopy
from typing import Union

from frozendict import frozendict

from EstablishmentCount import EstablishmentCount
from constants import activation_dict, BUILDING_ORDER
from constants import starting_buildings, landmarks_tuple, major_establishments_tuple, restaurants_tuple, \
    secondary_industry_dict, primary_industry_dict, building_cost
from player import Player


class Game(object):

    @staticmethod
    def _init_player(
            player_id: int = 0,
            starting_builds: frozendict = starting_buildings,
            starting_major_establishments: tuple = (),
    ) -> Player:
        return Player(
            id=player_id,
            coins=0,
            major_establishments={
                key: True if key in starting_major_establishments else False
                for key in major_establishments_tuple
            },
            landmarks={landmark: False for landmark in landmarks_tuple},
            establishments={
                key: EstablishmentCount(working=val[0])
                for key, val in starting_builds.items()
            },
            is_first_turn=True,
        )

    @staticmethod
    def _init_market(n_players: int = 2) -> dict:
        """Initialize the market with establishment cards."""
        market_dict = {landmark: n_players for landmark in landmarks_tuple}
        market_dict = {
            **market_dict,
            **{
                major_establishment: n_players
                for major_establishment in major_establishments_tuple
            },
        }
        for building in (
                list(primary_industry_dict.keys())
                + list(secondary_industry_dict.keys())
                + list(restaurants_tuple)
        ):
            market_dict[building] = 6

        return market_dict

    def __init__(self, n_players: int, pre_existing_players=None, name='', options=None):
        self.n_players = n_players
        self.players = {
            i: self._init_player(
                player_id=i,
                starting_builds=starting_buildings,
                starting_major_establishments=(),
            )
            for i in range(n_players)
        }
        self.market = self._init_market(n_players=n_players)
        self.current_player = 0
        self.current_turn = 0

        if 'full_record' in options and options['full_record'] != '':
            self.full_record = True
            if not os.path.exists(options['full_record']):
                with open(options['full_record'], 'w') as f:
                    writer = csv.writer(f)
                    writer.writerow(self.get_full_record_headers())
            self.full_record_file = open(options['full_record'], 'a')
            self.full_record_writer = csv.writer(self.full_record_file)
        else:
            self.full_record = False
        if 'use_max_probability' not in options:
            self.use_max_probability = False
        else:
            self.use_max_probability = options['use_max_probability']
        if 'prob_mod' not in options:
            self.prob_mod = 0.
        else:
            self.prob_mod = options['prob_mod']
        if not pre_existing_players:
            self.players = [Player(self, i, name) for i in range(4)]
            self.initialize_player_ai()
        else:
            random.shuffle(pre_existing_players)
            self.players = [player.reset_game(self, i) for i, player in enumerate(pre_existing_players)]


        self.id = id
        self.name = name
        # may be used for weighting
        self.turn = 0
        if 'game_record_filename' not in options:
            self.record_game = False
        elif options['game_record_filename'] != '':
            self.record_game = True
            self.game_record_file = open(options['game_record_filename'], 'a')
        else:
            self.record_game = False
        self.completed = False

    def run(self, silent=False):
        if not silent:
            print('Beginning game #%s' % self.id)
        if self.record_game:
            self.game_record_file.write('---BEGIN GAME %s---\n' % self.id)
        current_player = self.players[0]
        while True:
            self.turn += 1
            if self.record_game:
                self.game_record_file.write("BEGIN TURN %d\n" % self.turn)
            if self.full_record:
                self.record_full_game_state()
            current_player.take_turn()
            if current_player.win:
                break
            elif current_player.extra_turn:
                current_player.extra_turn = False
            else:
                current_player = self.get_next_player(current_player)
            if self.turn % 200 == 0 and not silent:
                print('turn %s' % self.turn)
                for player in self.players:
                    print(player.coins)
        if not silent:
            print('Player %d, order %d won in %d turns' % (current_player.id, current_player.order, self.turn))
        self.completed = True
        if self.record_game:
            self.game_record_file.write(
                'Player %d, order %d won in %d turns\n' % (current_player.id, current_player.order, self.turn))
            self.game_record_file.write('FINAL STANDINGS:\n')
            for player in self.players:
                self.game_record_file.write('+++++++++++++++++++++')
                self.game_record_file.write("PLAYER %d\n" % player.order)
                self.game_record_file.write("TOTAL COINS: %d\n" % player.coins)
                for building in BUILDING_ORDER:
                    self.game_record_file.write("%s COUNT: %d\n" % (building.upper(), player.buildings[building]))
            self.game_record_file.write('--------------------------------\n')
            self.game_record_file.close()
        if self.full_record:
            self.record_full_game_state()
            self.full_record_file.close()
        for player in self.players:
            player.update_win_history()
        if player.shared_ai:
            shared = player.AI.shared
            for player in self.players:
                shared.dice_history += player.dice_history
                shared.dice_history_win += player.dice_history_win
                shared.dice_history_turn += player.dice_history_turn
                shared.reroll_history += player.reroll_history
                shared.reroll_history_win += player.reroll_history_win
                shared.reroll_history_turn += player.reroll_history_turn
                shared.steal_history += player.steal_history
                shared.steal_history_win += player.steal_history_win
                shared.steal_history_turn += player.steal_history_turn
                shared.swap_history += player.swap_history
                shared.swap_history_win += player.swap_history_win
                shared.swap_history_turn += player.swap_history_turn
                shared.buy_history += player.buy_history
                shared.buy_history_win += player.buy_history_win
                shared.buy_history_turn += player.buy_history_turn
                player.flush_history(flush_shared=False)

        return self.players

    def flush_player_history(self):
        for player in self.players:
            player.flush_history()

    def initialize_player_ai(self):
        for player in self.players:
            player.initialize_ai()

    def get_next_player(self, player, offset=1):
        return self.players[(player.order + offset) % 4]

    def get_target_player_id(self, current_player_id: int) -> int:
        # just take from the richest
        target_player_id = sorted(
            [
                (player_id, self.players[player_id].coins)
                for player_id in self.players
                if player_id != current_player_id
            ],
            key=lambda a: a[1],
            reverse=True,
        )
        target_player_id = target_player_id[0][0]
        return target_player_id

    def get_reverse_player_order(self, player_id: int) -> list:
        order = [player_id - 1 if player_id - 1 >= 0 else self.n_players - 1]
        for _ in range(self.n_players - 1):
            if order[-1] == 0:
                order.append(self.n_players - 1)
            else:
                order.append(order[-1] - 1)

        return order[:-1]

    @staticmethod
    def roll_dice(num_dice=1) -> tuple[int, bool]:
        """Simulate rolling dice."""
        roll1 = random.randint(1, 6)
        roll2 = random.randint(1, 6) if num_dice == 2 else 0
        is_double = True if roll1 == roll2 else False
        return roll1 + roll2, is_double

    def activate_special_card(
            self,
            card_name: str,
            current_player_id: int,
            building_info: EstablishmentCount,
            **kwargs,
    ) -> None:
        match card_name:
            case "fruit_and_vegetable_market":
                total_wheat_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "wheat":
                        total_wheat_buildings += b_info.working
                coins_to_gain = 2 * total_wheat_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain

            case "cheese_factory":
                total_cow_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "cow":
                        total_cow_buildings += b_info.working
                coins_to_gain = 3 * total_cow_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain

            case "furniture_factory":
                total_gear_buildings = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if primary_industry_dict.get(b_name, "") == "gear":
                        total_gear_buildings += b_info.working
                coins_to_gain = 3 * total_gear_buildings
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain

            case "stadium":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for player_id in reverse_player_order:
                    coins_to_take = 2
                    coins_to_take *= building_info.working
                    coins_to_take = min(coins_to_take, self.players[player_id].coins)
                    self.players[player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case "tv_station":
                target_player_id = kwargs["target_player_id"]
                coins_to_take = 5
                coins_to_take *= building_info.working
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[current_player_id].coins += coins_to_take
            case "business_center":
                target_player_id = kwargs["target_player_id"]
                target_player_building = kwargs["target_player_building"]
                current_player_building = kwargs["current_player_building"]

                self.players[target_player_id].establishments[
                    target_player_building
                ].working -= 1

                b_info = self.players[target_player_id].establishments[
                    target_player_building
                ]
                if b_info.working == 0:
                    self.players[target_player_id].establishments.pop(
                        target_player_building
                    )

                if (target_player_building
                        in self.players[current_player_id].establishments):

                    self.players[current_player_id].establishments[
                        target_player_building
                    ].working += 1
                else:
                    self.players[current_player_id].establishments[
                        target_player_building
                    ] = EstablishmentCount(working=1)

                b_info = self.players[current_player_id].establishments[
                    current_player_building
                ]

                if b_info.working > 0:
                    self.players[current_player_id].establishments[
                        current_player_building
                    ].working -= 1

                b_info = self.players[current_player_id].establishments[
                    current_player_building
                ]
                if b_info == EstablishmentCount(working=0):
                    self.players[current_player_id].establishments.pop(
                        current_player_building)

                if (
                        current_player_building
                        in self.players[target_player_id].establishments
                ):

                    self.players[target_player_id].establishments[
                        current_player_building
                    ].working += 1
                else:
                    self.players[target_player_id].establishments[
                        current_player_building
                    ] = EstablishmentCount(working=1)
            case "tuna_boat":
                tuna_roll, _ = self.roll_dice(num_dice=2)
                coins_to_gain = tuna_roll * building_info.working
                self.players[current_player_id].coins += coins_to_gain
            case "flower_shop":
                flower_gardens = self.players[current_player_id].establishments.get(
                    "flower_garden",
                    EstablishmentCount(working=0),
                )
                flower_gardens = flower_gardens.working
                coins_to_gain = flower_gardens * building_info.working
                self.players[current_player_id].coins += coins_to_gain
            case "food_warehouse":
                total_restaurants = 0
                for b_name, b_info in self.players[
                    current_player_id
                ].establishments.items():
                    if b_name in restaurants_tuple:
                        total_restaurants += b_info.working
                coins_to_gain = total_restaurants * 2
                coins_to_gain *= building_info.working
                self.players[current_player_id].coins += coins_to_gain
            case "sushi_bar":
                target_player_id = kwargs["target_player_id"]
                receiving_player_id = kwargs["receiving_player_id"]
                coins_to_take = 3
                if self.players[receiving_player_id].landmarks["shopping_mall"]:
                    coins_to_take += 1
                if not self.players[receiving_player_id].landmarks["harbor"]:
                    coins_to_take = 0
                coins_to_take *= (
                    self.players[receiving_player_id]
                    .establishments["sushi_bar"]
                    .working
                )
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[receiving_player_id].coins += coins_to_take
            case "publisher":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    coins_to_take = 0
                    for b_name, b_info in self.players[
                        target_player_id
                    ].establishments.items():
                        if (
                                b_name in restaurants_tuple
                                or secondary_industry_dict.get(b_name, "") == "bread"
                        ):
                            coins_to_take += b_info.working
                    coins_to_take *= building_info.working
                    coins_to_take = min(
                        coins_to_take, self.players[target_player_id].coins
                    )
                    self.players[target_player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case "tax_office":
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    if self.players[target_player_id].coins >= 10:
                        coins_to_take = math.floor(
                            self.players[target_player_id].coins / 2
                        )
                        coins_to_take *= building_info.working
                        self.players[target_player_id].coins -= coins_to_take
                        self.players[current_player_id].coins += coins_to_take
            case _:
                pass

    def activate_cards(self, current_player_id: int, roll: int) -> None:
        """Activate cards based on dice roll."""
        # red goes first
        reverse_player_order = self.get_reverse_player_order(current_player_id)
        for player_id in reverse_player_order:
            has_shopping_mall = self.players[player_id].landmarks["shopping_mall"]
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if self.players[current_player_id].coins == 0:
                    continue
                if building_name not in restaurants_tuple:
                    continue
                if building_info.working == 0:
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue
                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    kwargs = {
                        "target_player_id": current_player_id,
                        "receiving_player_id": player_id,
                    }
                    self.activate_special_card(
                        building_name, -1, building_info, **kwargs
                    )
                    continue

                if has_shopping_mall:
                    coins_to_take += 1
                coins_to_take *= building_info.working
                coins_to_take = min(
                    coins_to_take, self.players[current_player_id].coins
                )
                self.players[current_player_id].coins -= coins_to_take
                print(
                    f"{current_player_id=} lost {coins_to_take=}, current player coins: {self.players[current_player_id].coins}"
                )
                self.players[player_id].coins += coins_to_take
                print(
                    f"{player_id=} gain {coins_to_take=}, current player coins: {self.players[player_id].coins}"
                )

        has_shopping_mall = self.players[current_player_id].landmarks["shopping_mall"]
        for building_name, building_info in self.players[
            current_player_id
        ].establishments.items():
            if building_name not in secondary_industry_dict:
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue
            if building_info.working == 0:
                continue

            coins_to_take = activation_dict[building_name]["value"]
            if coins_to_take == "special":
                self.activate_special_card(
                    building_name, current_player_id, building_info
                )
                continue

            if has_shopping_mall and secondary_industry_dict[building_name] == "bread":
                coins_to_take += 1

            coins_to_take *= building_info.working
            self.players[current_player_id].coins += coins_to_take

        # blue goes next
        for player_id in self.players:
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if building_name not in primary_industry_dict:
                    continue
                if building_info.working == 0:
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue

                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    self.activate_special_card(building_name, player_id, building_info)
                    continue

                coins_to_take *= building_info.working
                self.players[player_id].coins += coins_to_take

        # purple goes last
        for building_name in self.players[current_player_id].major_establishments:
            if building_name == "business_center":
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue

            kwargs = {}
            if building_name == "tv_station":
                kwargs["target_player_id"] = self.get_target_player_id(
                    current_player_id
                )

            self.activate_special_card(
                building_name,
                current_player_id,
                EstablishmentCount(working=1),
                **kwargs,
            )

        # special treatment for business center
        if (
                "business_center" in self.players[current_player_id].major_establishments
                and roll in activation_dict["business_center"]["roll"]
        ):
            kwargs: dict[str, Union[int, str]] = {
                "target_player_id": self.get_target_player_id(current_player_id)
            }
            choose_from = [
                key
                for key in self.players[
                    int(kwargs["target_player_id"])
                ].establishments.keys()
                if self.players[int(kwargs["target_player_id"])]
                   .establishments[key]
                   .working
                   > 0

            ]
            kwargs["target_player_building"] = random.choice(choose_from)
            kwargs["current_player_building"] = random.choice(
                list(
                    key
                    for key in self.players[current_player_id].establishments.keys()
                    if self.players[current_player_id].establishments[key].working > 0

                )
            )
            self.activate_special_card(
                "business_center",
                current_player_id,
                EstablishmentCount(working=1),
                **kwargs,
            )

    def clean_empty_cards(self) -> None:
        for player_id in self.players:
            to_pop = []
            for building_name, building_info in self.players[
                player_id
            ].establishments.items():
                if building_info == EstablishmentCount(working=0):
                    to_pop.append(building_name)
            for building_name in to_pop:
                self.players[player_id].establishments.pop(building_name)

    def take_turn(self) -> None:
        """Simulate one turn for the current player."""
        current_player_id = self.current_player
        is_double = False
        self.current_turn += 1
        print(f"START OF TURN {self.current_turn}")
        for player_id in self.players:
            print(f"\t{player_id=}, coins: {self.players[player_id].coins}")
        if not self.players[current_player_id].is_first_turn:
            # Step 1: Roll Dice
            num_dice = (
                1
                if not self.players[current_player_id].landmarks["train_station"]
                else random.choice([1, 2])
            )
            roll, is_double = self.roll_dice(num_dice)
            print(
                f"Player {current_player_id} rolled {roll} {'(which is double)' if is_double else ''}."
            )

            # Step 2: player can choose to reroll if they have radio tower
            if self.players[current_player_id].landmarks["radio_tower"]:
                do_reroll = bool(random.random() < 0.5)
                if do_reroll:
                    print(f"Player {current_player_id} chose to reroll")
                    num_dice = (
                        1
                        if not self.players[current_player_id].landmarks[
                            "train_station"
                        ]
                        else random.choice([1, 2])
                    )
                    roll, is_double = self.roll_dice(num_dice)
                    print(
                        f"Player {current_player_id} rolled {roll} {'(which is double)' if is_double else ''}."
                    )

            # Step 3: Activate Cards
            self.activate_cards(current_player_id, roll)
            # technical step: clean empty cards
            self.clean_empty_cards()
        self.players[current_player_id].is_first_turn = False

        # Step 4: Сity hall gives a coin if active player does not have any
        self.players[current_player_id].coins = (
            1
            if self.players[current_player_id].coins == 0
            else self.players[current_player_id].coins
        )

        # Step 5: Buy a card (randomly for now)
        possible_purchases = [
            card
            for card, count in self.market.items()
            if building_cost[card] <= self.players[current_player_id].coins
               and count > 0
               and not self.players[current_player_id].major_establishments.get(
                card, False
            )
               and not self.players[current_player_id].landmarks.get(card, False)
        ]
        print(f"{possible_purchases=}")
        has_built = False
        if possible_purchases:
            purchase = random.choice(possible_purchases)
            self.market[purchase] -= 1
            self.players[current_player_id].coins -= building_cost[purchase]
            if purchase in landmarks_tuple:
                self.players[current_player_id].landmarks[purchase] = True
            elif purchase in major_establishments_tuple:
                self.players[current_player_id].major_establishments[purchase] = True
            else:
                if purchase not in self.players[current_player_id].establishments:
                    self.players[current_player_id].establishments[purchase] = (
                        EstablishmentCount(
                            working=1
                        )
                    )
                else:
                    self.players[current_player_id].establishments[
                        purchase
                    ].working += 1
            has_built = True
            print(f"Player {current_player_id} bought {purchase}.")

        # Step 7: airport trigger
        if not has_built and self.players[current_player_id].landmarks["airport"]:
            self.players[current_player_id].coins += 10

        for player_id in self.players:
            print(
                f"\t{player_id=}, coins: {self.players[player_id].coins}, landmarks: {self.players[player_id].landmarks}"
            )
        if is_double and self.players[current_player_id].landmarks["amusement_park"]:
            # no reason not to take a second turn
            pass
        else:
            self.current_player = (self.current_player + 1) % self.n_players

    def is_game_over(self):
        """Check if a player has won."""
        for player_id in self.players:
            if all(
                    self.players[player_id].landmarks.values()
            ):  # All landmarks completed
                return True, player_id
        return False, -1

    def play_game(self):
        """Simulate a full game."""
        is_game_over, winning_player_id = self.is_game_over()
        while not is_game_over:
            self.take_turn()
            print(f"--- End of turn {self.current_turn} ---")
            is_game_over, winning_player_id = self.is_game_over()
        print("Game over!")
        print(f"Player {winning_player_id} wins!")

    def train_players(self):
        for player in self.players:
            player.train_ai()

    def get_full_record_headers(self):
        """
		game#, turn#, buildings, coins, win for each player
		2 + 4*(18+2) = 82
		"""
        header = ['game_id', 'turn_id']
        for i in range(4):
            header += [('p%d_' % i) + x for x in (BUILDING_ORDER + ['coins', 'win'])]
        return header

    def record_full_game_state(self):
        # the completed boolean will
        vals = [self.id, self.turn + self.completed]
        for player in self.players:
            for building in BUILDING_ORDER:
                vals.append(player.buildings[building])
            vals += [player.coins, player.win]
        self.full_record_writer.writerow(vals)
