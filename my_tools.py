"""
This is the tools file. It contains functions and classes not tied directly to the execution
of the game or the game's sprites, but used in other files.
"""

from math import sin, cos, radians


class Force:
    """
    A force with a direction and magnitude

    :param direction: the direction of the force
    :param magnitude: the magnitude of the force
    :param magnitude_falloff: how quickly the magnitude is lowered. A lower number means a faster falloff. must be less
    than 1
    """

    def __init__(self, direction: float, magnitude: float, magnitude_falloff: float):

        if magnitude_falloff >= 1:
            raise ValueError(f"Magnitude must be less than 1, actual: {magnitude_falloff}")

        self._direction = direction
        self._magnitude = magnitude
        self._magnitude_falloff = magnitude_falloff

        self._change_x = cos(radians(direction)) * magnitude
        self._change_y = sin(radians(direction)) * magnitude

    @property
    def direction(self):
        return self._direction

    @property
    def magnitude(self):
        return self._magnitude

    @property
    def magnitude_falloff(self):
        return self._magnitude_falloff

    @property
    def change_x(self):
        return self._change_x

    @property
    def change_y(self):
        return self._change_y

    def update(self):

        self._magnitude *= self.magnitude_falloff
