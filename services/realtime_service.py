# Realtime prediction services

import collections
import numpy as np

class RealtimeSession:
    def __init__(self, sequence_length: int):
        self.sequence = collections.deque(maxlen=sequence_length)
        self.frames_collected = 0

    def add_frame(self, features: np.ndarray):
        self.sequence.append(features)
        self.frames_collected = len(self.sequence)

    def is_ready(self) -> bool:
        return self.frames_collected == self.sequence.maxlen

    def get_sequence(self) -> np.ndarray:
        return np.array(self.sequence)

    def reset(self):
        self.sequence.clear()
        self.frames_collected = 0