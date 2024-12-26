import keras
import numpy as np
from keras.layers import Dense, Dropout, Activation
from keras.models import Sequential


class SharedAI:
    """
    This class manages shared history data across multiple players and assigns shared AI attributes.
    """

    def __init__(self, player_list):
        """
        Initializes shared attributes and assigns the first player's AI as a reference for others.
        """
        for player in player_list:
            player.shared_ai = True
        base_player = player_list[0]
        self.ai = ai = base_player.AI
        self.player_id = base_player.id
        for player in player_list:
            player.AI.dice_ai = ai.dice_ai
            player.AI.swap_ai = ai.swap_ai
            player.AI.steal_ai = ai.steal_ai
            player.AI.buy_ai = ai.buy_ai
            player.AI.reroll_ai = ai.reroll_ai
            player.AI.add_ai = ai.add_ai
            player.AI.shared = self

        # Initialize history lists
        self.history = {
            "dice": [], "dice_win": [], "dice_turn": [],
            "reroll": [], "reroll_win": [], "reroll_turn": [],
            "steal": [], "steal_win": [], "steal_turn": [],
            "swap": [], "swap_win": [], "swap_turn": [],
            "buy": [], "buy_win": [], "buy_turn": [],
            "add": [], "add_win": [], "add_turn": [],

        }


class PlayerAI:
    """
    This class manages the AI for a player, including training and action recording.
    """

    def __init__(self, player):
        self.player = player
        self.game = self.player.game
        self.n_epochs = 5
        self.construct_input()

    def initialize_ai(self):
        """Initializes the AI by constructing the input and models."""
        self.input_dim = len(self.current_input)
        self.dice_ai = self.construct_ai(1)
        self.buy_ai = self.construct_ai(19)
        self.swap_ai = self.construct_ai(12 * 36)
        self.steal_ai = self.construct_ai(3)
        self.reroll_ai = self.construct_ai(1 + 1 + 12)
        self.add_ai = self.construct_ai(1 + 12)

    def train(self):
        """Trains each of the four AI models."""
        player = self.player if not self.player.shared_ai else self.shared

        for action in ["dice", "swap", "reroll", "buy", "steal", "add"]:
            history = player.__dict__.get(f"{action}_history", [])
            if history:
                x = np.asarray(history)[:, 0, :]
                y = keras.utils.to_categorical(player.__dict__.get(f"{action}_history_win"), 2)
                getattr(self, f"{action}_ai").fit(x, y, epochs=10, batch_size=100, verbose=0)

    def record_action(self, action, extra_input, right_input=None):
        """Generic method to record actions and append them to the appropriate history."""
        input_data = self.merge_input(extra_input)
        if right_input is not None:
            input_data = self.merge_right(input_data, right_input)

        if self.player.shared_ai:
            self.shared.history[f"{action}_history"].append(input_data)
            self.shared.history[f"{action}_turn"].append(self.player.game.turn)
        else:
            self.player.history[f"{action}_history"].append(input_data)
            self.player.history[f"{action}_turn"].append(self.player.game.turn)

    def eval_action(self, action, extra_input, right_input=None):
        """Generic method to evaluate actions using the respective AI."""
        input_data = self.merge_input(extra_input)
        if right_input is not None:
            input_data = self.merge_right(input_data, right_input)

        preds = getattr(self, f"{action}_ai").predict(input_data)
        return preds[:, 1]

    def merge_input(self, extra_input):
        """Merges the current input with additional input."""
        self.construct_input()
        extra_input_height = extra_input.shape[0]
        return np.column_stack((np.repeat([self.current_input], extra_input_height, 0), extra_input))

    def merge_right(self, original_input, right_input):
        """Merges the right input with the original input."""
        input_height = original_input.shape[0]
        return np.column_stack((original_input, np.repeat([right_input], input_height, 0)))

    def construct_input(self):
        """Constructs input for each player state."""
        self.current_input = self.player.complete_serialize()

    def construct_ai(self, additional_inputs):
        """Generates a generic AI model."""
        ai = Sequential([
            Dense(512, input_shape=(self.input_dim + additional_inputs,)),
            Dropout(0.1),
            Activation('relu'),
            Dense(256),
            Dropout(0.05),
            Activation('relu'),
            Dense(128),
            Dropout(0.05),
            Activation('relu'),
            Dense(2),
            Activation('softmax')
        ])
        opt = keras.optimizers.SGD(nesterov=True, momentum=0.1)
        ai.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
        return ai
