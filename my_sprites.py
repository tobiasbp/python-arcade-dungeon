import arcade
import math


class Enemy(arcade.Sprite):
    """
    parent class for all enemies in the game
    """

    def __init__(self, filename: str, center_pos: tuple[float, float], max_hp: int, speed: float, scale=1.0):

        super().__init__(
            filename=filename,
            scale=scale,
            center_x=center_pos[0],
            center_y=center_pos[1]
        )

        # hp
        self._max_hp = max_hp
        self.cur_hp = max_hp

        self.speed = speed

        # pathfinding
        self.path = []
        self.cur_path_position = 0  # which point on the path we are heading for.

    @property
    def max_hp(self):
        return self._max_hp

    def find_path(self, barrier_list: arcade.AStarBarrierList, target_pos: tuple[int, int]):
        """
        calculates a path to the target pos. Sets the sprite's path to this path.
        If an enemy has a path, it will automatically follow it.
        """

        # calculate the path. It will be a list of positions(lists)
        self.path = arcade.astar_calculate_path(self.position,
                                                target_pos,
                                                barrier_list,
                                                diagonal_movement=True)

        # reset this because we are at the start of a new path
        self.cur_path_position = 0

    def on_update(self, delta_time: float = 1 / 60):

        # follow the path, if present
        if self.path:

            # next position to move to
            dest_pos = self.path[self.cur_path_position]

            # calculate angle to next point
            angle_to_dest = arcade.get_angle_degrees(dest_pos[0], dest_pos[1], self.center_x, self.center_y)

            # calculate distance
            distance_to_dest = arcade.get_distance(dest_pos[0], dest_pos[1], self.center_x, self.center_y)

            # this is so we don't move too far
            this_move = min(self.speed, distance_to_dest)

            # if we are there, set the next position to move to
            if distance_to_dest <= self.speed:
                self.cur_path_position += 1

                # if we are finished with this path, stand still
                if self.cur_path_position >= len(self.path):
                    self.path = []

            self.change_x = math.cos(angle_to_dest) * this_move
            self.change_y = math.sin(angle_to_dest) * this_move

        self.center_x += self.change_x
        self.center_y += self.change_y

        # keep track of hp
        self.cur_hp = min(self.cur_hp, self.max_hp)

        # check if dead
        if self.cur_hp <= 0:
            self.kill()


class Enemy(arcade.Sprite):
    """
    parent class for all enemies in the game
    """

    def __init__(self, filename, center_x, center_y, max_hp, scale=1.0):

        super().__init__(
            filename=filename,
            scale=scale,
            center_x=center_y,
            center_y=center_x
        )

        self.max_hp = max_hp
        self.cur_hp = max_hp
        self.path = None

    def find_path(self, barrier_list: arcade.AStarBarrierList, target_pos: tuple[int, int]):
        """
        calculates a path to the target pos. Sets the sprite's path to this path.
        """

        self.path = arcade.astar_calculate_path(self.position,
                                                target_pos,
                                                barrier_list,
                                                diagonal_movement=True)

    def on_update(self, delta_time: float = 1 / 60):

        self.center_x += self.change_x
        self.center_y += self.change_y

        self.cur_hp = min(self.cur_hp, self.max_hp)

        if self.cur_hp <= 0:
            self.kill()

class Player(arcade.Sprite):
    """
    The player
    """

    def __init__(self, min_x_pos, max_x_pos, center_x=0, center_y=0, scale=1):
        """
        Setup new Player object
        """

        # Limits on player's x position
        self.min_x_pos = min_x_pos
        self.max_x_pos = max_x_pos

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            filename="images/tiny_dungeon/Tiles/tile_0109.png",
            scale=scale,
        )

    def on_update(self, delta_time):
        """
        Move the sprite
        """

        # Update player's x position based on current speed in x dimension
        self.center_x += delta_time * self.change_x

        # Enforce limits on player's x position
        if self.left < self.min_x_pos:
            self.left = self.min_x_pos
        elif self.right > self.max_x_pos:
            self.right = self.max_x_pos


class PlayerShot(arcade.Sprite):
    """
    A shot fired by the Player
    """

    def __init__(self, center_x, center_y, max_y_pos, speed=4, scale=1, start_angle=90):
        """
        Setup new PlayerShot object
        """

        # Set the graphics to use for the sprite
        # We need to flip it so it matches the mathematical angle/direction
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            scale=scale,
            filename="images/tiny_dungeon/Tiles/tile_0109.png",
            flipped_diagonally=True,
            flipped_horizontally=True,
            flipped_vertically=False,
        )

        # The shoot will be removed when it is above this y position
        self.max_y_pos = max_y_pos

        # Shoot points in this direction
        self.angle = start_angle

        # Shot moves forward. Sets self.change_x and self.change_y
        self.forward(speed)

    def on_update(self, delta_time):
        """
        Move the sprite
        """

        # Update the position of the sprite
        self.center_x += delta_time * self.change_x
        self.center_y += delta_time * self.change_y

        # Remove shot when over top of screen
        if self.bottom > self.max_y_pos:
            self.kill()
