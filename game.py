import csv
import math
import os
import random
from typing import Union

from frozendict import frozendict

from Building import Building
from BuildingType import BuildingType
from constants import activation_dict, player_limit
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
        player = Player()
        player.id = player_id
        player.buildings = {}
        for major_establishment in major_establishments_tuple:
            player.buildings[major_establishment] = 1 if major_establishment in starting_major_establishments else 0
        for landmark in landmarks_tuple:
            player.buildings[landmark] = 0
        for establishment in starting_builds:
            player.buildings[establishment] = starting_builds[establishment]
        player.coins = 0
        player.is_first_turn = True
        return player

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
        self.current_player_id = 0
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
            self.players = [Player(self, i, name) for i in range(5)]
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
                for building in Building:
                    self.game_record_file.write("%s COUNT: %d\n" % (building, player.buildings[building]))
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
            card_name: Building,
            current_player_id: int,
            building_count: int,
            **kwargs,
    ) -> None:
        current_player = self.players[current_player_id]

        match card_name:
            case Building.FRUIT_AND_VEGETABLE_MARKET:
                total_wheat_buildings = 0
                for b_name, b_count in current_player.buildings.items():
                    if primary_industry_dict.get(b_name, "") == BuildingType.WHEAT:
                        total_wheat_buildings += b_count
                coins_to_gain = 2 * total_wheat_buildings
                coins_to_gain *= building_count
                current_player.coins += coins_to_gain

            case Building.CHEESE_FACTORY:
                total_cow_buildings = 0
                for b_name, b_count in current_player.buildings.items():
                    if primary_industry_dict.get(b_name, "") == BuildingType.COW:
                        total_cow_buildings += b_count
                coins_to_gain = 3 * total_cow_buildings
                coins_to_gain *= building_count
                current_player.coins += coins_to_gain

            case Building.FURNITURE_FACTORY:
                total_gear_buildings = 0
                for b_name, b_count in current_player.buildings.items():
                    if primary_industry_dict.get(b_name, "") == BuildingType.GEAR:
                        total_gear_buildings += b_count
                coins_to_gain = 3 * total_gear_buildings
                coins_to_gain *= building_count
                self.players[current_player_id].coins += coins_to_gain

            case Building.STADIUM:
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for player_id in reverse_player_order:
                    coins_to_take = 2
                    coins_to_take *= building_count
                    coins_to_take = min(coins_to_take, self.players[player_id].coins)
                    self.players[player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case Building.TV_STATION:
                target_player_id = kwargs["target_player_id"]
                coins_to_take = 5
                coins_to_take *= building_count
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[current_player_id].coins += coins_to_take
            case Building.BUSINESS_CENTER:
                target_player_id = kwargs["target_player_id"]
                target_player_building = kwargs["target_player_building"]
                current_player_building = kwargs["current_player_building"]

                self.players[target_player_id].building[
                    target_player_building
                ] -= 1

                b_count = self.players[target_player_id].building[
                    target_player_building
                ]
                if b_count == 0:
                    self.players[target_player_id].building.pop(
                        target_player_building
                    )

                if (target_player_building
                        in self.players[current_player_id].buildings):

                    self.players[current_player_id].buildings[
                        target_player_building
                    ] += 1
                else:
                    self.players[current_player_id].buildings[
                        target_player_building
                    ] = 1

                b_count = self.players[current_player_id].buildings[
                    current_player_building
                ]

                if b_count > 0:
                    self.players[current_player_id].buildings[
                        current_player_building
                    ] -= 1

                b_count = self.players[current_player_id].buildings[
                    current_player_building
                ]
                if b_count == 0:
                    self.players[current_player_id].buildings.pop(
                        current_player_building)

                if current_player_building in self.players[target_player_id].buildings:
                    self.players[target_player_id].buildings[
                        current_player_building
                    ] += 1
                else:
                    self.players[target_player_id].building[
                        current_player_building
                    ] = 1
            case Building.TUNA_BOAT:
                tuna_roll, _ = self.roll_dice(num_dice=2)
                coins_to_gain = tuna_roll * building_count
                self.players[current_player_id].coins += coins_to_gain
            case Building.FLOWER_SHOP:
                current_player.coins += building_count * current_player.buildings.get(
                    Building.FLOWER_GARDEN,
                    0,
                )
            case Building.FOOD_WAREHOUSE:

                total_restaurants = 0
                for b_name, b_count in current_player.building.items():
                    if b_name in restaurants_tuple:
                        total_restaurants += b_count

                current_player.coins += total_restaurants * building_count * 2
            case Building.SUSHI_BAR:
                target_player_id = kwargs["target_player_id"]
                receiving_player_id = kwargs["receiving_player_id"]
                coins_to_take = 3
                if self.players[receiving_player_id].buildings[Building.SHOPPING_MALL]:
                    coins_to_take += 1
                if not self.players[receiving_player_id].buildings[Building.HARBOR]:
                    coins_to_take = 0
                coins_to_take *= (
                    self.players[receiving_player_id]
                    .buildings[Building.SUSHI_BAR]
                )
                coins_to_take = min(coins_to_take, self.players[target_player_id].coins)
                self.players[target_player_id].coins -= coins_to_take
                self.players[receiving_player_id].coins += coins_to_take
            case Building.PUBLISHER:
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    coins_to_take = 0
                    for b_name, b_count in self.players[
                        target_player_id
                    ].building.items():
                        if (
                                b_name in restaurants_tuple
                                or secondary_industry_dict.get(b_name, "") == BuildingType.BREAD
                        ):
                            coins_to_take += b_count
                    coins_to_take *= building_count
                    coins_to_take = min(
                        coins_to_take, self.players[target_player_id].coins
                    )
                    self.players[target_player_id].coins -= coins_to_take
                    self.players[current_player_id].coins += coins_to_take
            case Building.TAX_OFFICE:
                reverse_player_order = self.get_reverse_player_order(current_player_id)
                for target_player_id in reverse_player_order:
                    if self.players[target_player_id].coins >= 10:
                        coins_to_take = math.floor(
                            self.players[target_player_id].coins / 2
                        )
                        coins_to_take *= building_count
                        self.players[target_player_id].coins -= coins_to_take
                        self.players[current_player_id].coins += coins_to_take
            case _:
                pass

    def activate_cards(self, current_player_id: int, roll: int) -> None:
        """Activate cards based on dice roll."""
        # red goes first
        current_player = self.players[current_player_id]
        reverse_player_order = self.get_reverse_player_order(current_player_id)
        for player_id in reverse_player_order:
            has_shopping_mall = self.players[player_id].buildings[Building.SHOPPING_MALL]
            for building_name, building_count in self.players[
                player_id
            ].buildings.items():
                if self.players[current_player_id].coins == 0:
                    continue
                if building_name not in restaurants_tuple:
                    continue
                if building_count == 0:
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
                        building_name, -1, building_count, **kwargs
                    )
                    continue

                if has_shopping_mall:
                    coins_to_take += 1
                coins_to_take *= building_count
                coins_to_take = min(
                    coins_to_take, self.players[current_player_id].coins
                )
                self.players[current_player_id].coins -= coins_to_take
                print(
                    f"{current_player_id=} lost {coins_to_take=}, "
                    f"current player coins: {self.players[current_player_id].coins}"
                )
                self.players[player_id].coins += coins_to_take
                print(
                    f"{player_id=} gain {coins_to_take=}, current player coins: {self.players[player_id].coins}"
                )

        has_shopping_mall = self.players[current_player_id].buildings[Building.SHOPPING_MALL]
        for building_name, building_count in self.players[
            current_player_id
        ].buildings.items():
            if building_name not in secondary_industry_dict:
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue
            if building_count == 0:
                continue

            coins_to_take = activation_dict[building_name]["value"]
            if coins_to_take == "special":
                self.activate_special_card(
                    building_name, current_player_id, building_count
                )
                continue

            if has_shopping_mall and secondary_industry_dict[building_name] == BuildingType.BREAD:
                coins_to_take += 1

            coins_to_take *= building_count
            self.players[current_player_id].coins += coins_to_take

        # blue goes next
        for player_id in self.players:
            for building_name, building_count in self.players[
                player_id
            ].building.items():
                if building_name not in primary_industry_dict:
                    continue
                if building_count == 0:
                    continue
                if roll not in activation_dict[building_name]["roll"]:
                    continue

                coins_to_take = activation_dict[building_name]["value"]
                if coins_to_take == "special":
                    self.activate_special_card(building_name, player_id, building_count)
                    continue

                coins_to_take *= building_count
                self.players[player_id].coins += coins_to_take

        # purple goes last
        for building_name in major_establishments_tuple:
            if current_player.buildings.get(building_name, 0) == 0:
                continue
            if building_name == Building.BUSINESS_CENTER:
                continue
            if roll not in activation_dict[building_name]["roll"]:
                continue

            kwargs = {}
            if building_name == Building.TV_STATION:
                kwargs["target_player_id"] = current_player.decide_target_tv_station()

            self.activate_special_card(
                building_name,
                current_player_id,
                1,
                **kwargs,
            )

        # special treatment for business center
        if (
                Building.BUSINESS_CENTER in current_player.buildings
                and roll in activation_dict[Building.BUSINESS_CENTER]["roll"]
        ):
            kwargs: dict[str, Union[int, str]] = {
                "target_player_id": current_player.decide_target_business_center()
            }
            choose_from = [
                key
                for key in self.players[
                    int(kwargs["target_player_id"])
                ].buildings.keys()
                if self.players[int(kwargs["target_player_id"])].buildings[key] > 0

            ]
            kwargs["target_player_building"] = random.choice(choose_from)
            kwargs["current_player_building"] = random.choice(
                list(
                    key
                    for key in self.players[current_player_id].buildings.keys()
                    if self.players[current_player_id].buildings[key] > 0

                )
            )
            self.activate_special_card(
                Building.BUSINESS_CENTER,
                current_player_id,
                1,
                **kwargs,
            )

    def clean_empty_cards(self) -> None:
        for player_id in self.players:
            to_pop = []
            for building_name, building_count in self.players[
                player_id
            ].building.items():
                if building_count == 0:
                    to_pop.append(building_name)
            for building_name in to_pop:
                self.players[player_id].buildings.pop(building_name)

    def take_turn(self) -> None:
        """Simulate one turn for the current player."""
        current_player_id = self.current_player_id
        current_player = self.players[current_player_id]
        is_double = False
        self.current_turn += 1
        print(f"START OF TURN {self.current_turn}")
        for player_id in self.players:
            print(f"\t{player_id=}, coins: {self.players[player_id].coins}")
        if not self.players[current_player_id].is_first_turn:
            # Step 1: Roll Dice
            num_dice = current_player.decide_dice()
            roll, is_double = self.roll_dice(num_dice)
            print(
                f"Player {current_player_id} rolled {roll} {'(which is double)' if is_double else ''}."
            )

            # Step 2: player can choose to reroll if they have radio tower
            if current_player.buildings[Building.RADIO_TOWER]:
                do_reroll = current_player.decide_reroll()
                if do_reroll:
                    print(f"Player {current_player_id} chose to reroll")
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

        # Step 5: Buy a card
        possible_purchases = [
            card
            for card, count in self.market.items()
            if building_cost[card] <= current_player.coins
               and count > 0
               and not current_player.buildings.get(card, 0) == player_limit[card]
        ]
        print(f"{possible_purchases}")
        has_built = False
        if possible_purchases:
            purchase = current_player.decide_purchase(possible_purchases)
            self.market[purchase] -= 1
            current_player.coins -= building_cost[purchase]
            current_player.buildings[purchase] = current_player.buildings.get(purchase,0) + 1
            has_built = True
            print(f"Player {current_player_id} bought {purchase}.")

        # Step 7: airport trigger
        if not has_built and current_player.buildings[Building.AIRPORT]:
            current_player.coins += 10

        for player_id in self.players:
            print(
                f"\t{player_id=}, coins: {self.players[player_id].coins}, "
                f"buildings: {self.players[player_id].buildings}"
            )
        if is_double and current_player.buildings[Building.AMUSEMENT_PARK]:
            # no reason not to take a second turn (LIE)
            pass
        else:
            self.current_player_id = (self.current_player_id + 1) % self.n_players

    def is_game_over(self):
        """Check if a player has won."""
        for player_id in self.players:
            win = True
            for landmark in landmarks_tuple:
                if not self.players[player_id].buildings[landmark]:
                    win = False
                    break
            if win:
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