import numpy as np
import tensorflow as tf
from tensorflow.keras.layers import Input, Dense, Dropout, Activation
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.optimizers import SGD

input_sizes = {
    'dice': 1,
    'buy': 19,
    'swap': 12 * 36,
    'steal': 3,
    'reroll': 1 + 1 + 12,
    'add': 1 + 12
}
actions = list(input_sizes.keys())


class PlayerAI:
    """
    This class manages the AI for a player, including training and action recording.
    """

    def __init__(self, player):
        self.player = player
        self.game = self.player.game
        self.n_epochs = 5
        self.construct_input()

        self.input_dim = None
        self.models = {}

        self.history = {}
        for action in actions:
            self.history[action] = []
            self.history[action + '_win'] = []
            self.history[action + '_turn'] = []

    def initialize_ai(self):
        """Initializes the AI by constructing the input and models."""
        self.input_dim = len(self.current_input)
        for action in actions:
            self.models[action] = self.create_model(input_sizes[action])

    def train(self):
        """Trains each of the five AI models."""
        player = self.player

        for action in actions:
            history = self.history[action]  # player.__dict__.get(f"{action}_history", [])
            if history:
                x = np.asarray(history)[:, 0, :]
                y = tf.keras.utils.to_categorical(player.__dict__.get(f"{action}_history_win"), 2)
                self.models[action].fit(x, y, epochs=10, batch_size=100, verbose=0)

    def record_action(self, action, extra_input, right_input=None):
        """Generic method to record actions and append them to the appropriate history."""
        input_data = self.merge_input(extra_input)
        if right_input is not None:
            input_data = self.merge_right(input_data, right_input)

        self.player.history[f"{action}_history"].append(input_data)
        self.player.history[f"{action}_turn"].append(self.player.game.turn)

    def eval_action(self, action, extra_input, right_input=None):
        """Generic method to evaluate actions using the respective AI."""
        input_data = self.merge_input(extra_input)
        if right_input is not None:
            input_data = self.merge_right(input_data, right_input)

        preds = self.models[action].predict(input_data)
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

    def load(self, prefix):
        for action in actions:
            self.models[action] = load_model(f"{prefix}{action}_ai.h5")

    def save(self, prefix):
        for action in actions:
            self.models[action].save(f"{prefix}{action}_ai.h5")

    def create_model(self, additional_inputs):
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
        opt = SGD(nesterov=True, momentum=0.1)
        ai.compile(loss='categorical_crossentropy', optimizer=opt, metrics=['accuracy'])
        return ai
