import arcade
import math
import random
from typing import List
from enum import IntEnum

class Enemy(arcade.Sprite):
    """
    parent class for all enemies in the game. Features include pathfinding, hp management and movement

    :param filename: path to the file used as graphics for the sprite.
    :param position: tuple containing the x and y coordinate to create the sprite at.
    :param max_hp: the max hp for the enemy. Also determines starting hp.
    :param speed: the movement speed for the sprite in px/update.
    :param scale: the size multiplier for the graphics/hitbox of the sprite.
    """

    def __init__(
            self,
            position: tuple[float, float],
            impassables: arcade.SpriteList,
            window: arcade.Window,
            grid_size: int,
            filename: str = "images/tiny_dungeon/Tiles/tile_0087.png",
            max_hp: int = 10,
            speed: int = 1,
            scale: float = 1.0):

        super().__init__(
            filename=filename,
            scale=scale,
            center_x=position[0],
            center_y=position[1]
        )

        # hp
        self._max_hp = max_hp
        self.cur_hp = max_hp

        self.speed = speed

        # pathfinding
        self.path = []
        self.cur_path_position = 0  # which point on the path we are heading for.

        # create our own map of barriers
        self.barriers = arcade.AStarBarrierList(
            moving_sprite=self,
            blocking_sprites=impassables,
            grid_size=grid_size,
            left=0,
            right=window.width,
            bottom=0,
            top=window.height
        )

    @property
    def max_hp(self):
        return self._max_hp

    def go_to_position(self, target_pos: tuple[int, int]):
        """
        calculates a path to the target pos. Sets the sprite's path to this path.
        If an enemy has a path, it will automatically follow it.
        If no barrier list is given, use the sprites own barriers.
        """

        # calculate the path. It will be a list of positions(lists)
        self.path = arcade.astar_calculate_path(self.position,
                                                target_pos,
                                                self.barriers,
                                                diagonal_movement=True)

        # reset this because we are at the start of a new path
        self.cur_path_position = 0

    def on_update(self, delta_time: float = 1 / 60):

        if not self.path:

            # reset movement vectors, so we stop when a path is finished
            self.change_x = 0
            self.change_y = 0

        # follow the path, if present
        else:

            # next position to move to
            dest_pos = self.path[self.cur_path_position]

            # calculate angle to next point
            angle_to_dest = arcade.get_angle_radians(dest_pos[0], dest_pos[1], self.center_x, self.center_y)

            # calculate distance
            distance_to_dest = arcade.get_distance(dest_pos[0], dest_pos[1], self.center_x, self.center_y)

            # this is so we don't move too far
            this_move_length = min(self.speed, distance_to_dest)

            # if we are there, set the next position to move to
            if distance_to_dest <= self.speed:
                self.cur_path_position += 1

                # if we are finished with this path, stand still
                if self.cur_path_position == len(self.path):
                    self.path = []

            else:
                # testing shows that we need to reverse the direction...
                self.center_x += -math.sin(angle_to_dest) * this_move_length
                self.center_y += -math.cos(angle_to_dest) * this_move_length

        # make sure hp cannot exceed max_hp
        self.cur_hp = min(self.cur_hp, self.max_hp)

        # remove the sprite if hp is 0 or less
        if self.cur_hp <= 0:
            self.kill()


class Player(arcade.Sprite):
    """
    The player
    """

    def __init__(
            self,
            center_x=0,
            center_y=0,
            speed=2,
            scale=1,
            key_up=arcade.key.UP,
            key_down=arcade.key.DOWN,
            key_left=arcade.key.LEFT,
            key_right=arcade.key.RIGHT,
            key_attack=arcade.key.SPACE
        ):
        """
        Setup new Player object
        """

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            filename="images/tiny_dungeon/Tiles/tile_0109.png",
            scale=scale,
        )

        self.speed = speed

        # We need this to scale the Emotes
        self.scale = scale

        self.key_left = key_left
        self.key_right = key_right
        self.key_up = key_up
        self.key_down = key_down
        self.key_atttack = key_attack

        # Track state of controls (could also be a joystick in the future)
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.atttack_pressed = False

        # Player's emotes will be stored here
        self._emotes = arcade.SpriteList()

    def react(self, reaction):
        """
        Add an Emote
        """
        self._emotes.append(
            Emote(
                reaction=reaction,
                position=self.position,
                scale=self.scale
            )
        )

    @property
    def emotes(self):
        return self._emotes

    def on_key_press(self, key, modifiers):
        """
        Track the state of the control keys
        """
        if key == self.key_left:
            self.left_pressed = True
        elif key == self.key_right:
            self.right_pressed = True
        elif key == self.key_up:
            self.up_pressed = True
        elif key == self.key_down:
            self.down_pressed = True
        elif key == self.key_atttack:
            self.atttack_pressed = True


    def on_key_release(self, key, modifiers):
        """
        Track the state of the control keys
        """
        if key == self.key_left:
            self.left_pressed = False
        elif key == self.key_right:
            self.right_pressed = False
        elif key == self.key_up:
            self.up_pressed = False
        elif key == self.key_down:
            self.down_pressed = False
        elif key == self.key_atttack:
            self.atttack_pressed = False


    def update(self):
        """
        Set Sprite's speed based on key status
        """
        # Assume no keys are held
        self.change_x = 0
        self.change_y = 0

        # Update speed based on held keys
        if self.left_pressed and not self.right_pressed:
            self.change_x = -1 * self.speed
        elif self.right_pressed and not self.left_pressed:
            self.change_x = self.speed
        elif self.up_pressed and not self.down_pressed:
            self.change_y = self.speed
        elif self.down_pressed and not self.up_pressed:
            self.change_y = -1 * self.speed

        # Note: We don't change the position of the sprite here, since that is done by the physics engine


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


class Reaction(IntEnum):
    """
    Reaction names that map to Emote graphics
    """
    HEART_BROKEN = 4
    HEART = 5
    EXCLAMATION_BLACK = 7
    EXCLAMATION_RED = 8
    HAPPY = 13
    SAD = 14
    ANGRY = 15
    NOTE = 10
    LAUGH = 28


class Emote(arcade.Sprite):
    """
    An emote to show the emotion of a character in the game.
    It will delete itself after lifetime has passed.
    """

    # A list of emotes as textures from a sprite sheet
    emotes: List[arcade.texture.Texture] = arcade.load_spritesheet(
        file_name = "data/emotes/pixel_style2.png",
        sprite_width=16,
        sprite_height=16,
        columns=10,
        count=30)

    def __init__(
            self,
            reaction: Reaction,
            position: tuple[int, int],
            offset_x:int = 0,
            offset_y:int = 16,
            float_x:float=0.1,
            float_y:float=0.2,
            scale:int=1,
            lifetime:float = 5.0,
            enable_fade=True):

        # The emote will disapear after this many seconds
        self.lifetime = lifetime
        self.time_left = lifetime

        self.enable_fade = enable_fade

        super().__init__(
            center_x = position[0],
            center_y = position[1],
            scale = scale,
            texture = Emote.emotes[reaction]
        )

        self.change_x = random.uniform(-1 * float_x, float_x)
        self.change_y = float_y

    def on_update(self, delta_time:float):

        self.center_x += self.change_x
        self.center_y += self.change_y

        self.time_left -= delta_time

        if self.enable_fade:
            self.alpha = max(0, 255 * self.time_left/self.lifetime)

        if self.time_left <= 0:
            self.kill()