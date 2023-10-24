import arcade
import math
import random
from typing import List, Optional
from enum import IntEnum, Enum, auto, unique

@unique
class EnemyState(Enum):
    """
    All possible states for enemies
    """

    ROAMING = auto()
    CHASING = auto()


class Attack(arcade.Sprite):
    """
    A simple hitbox to track collisions with. Just has a hitbox and a duration.

    :param duration: the maximum lifetime of the sprite. Kills this number of seconds after creation.
    :param damage: the amount of damage to inflict upon each target's hp, upon collision.
    """

    def __init__(self, duration: float, damage: int, **kwargs):
        super().__init__(**kwargs)

        self.duration = duration
        self.damage = damage

        self.timer = 0

    def on_update(self, delta_time: float = 1 / 60):

        # if duration is up, remove self
        self.timer += delta_time
        if self.timer > self.duration:
            self.kill()


class Enemy(arcade.Sprite):
    """
    parent class for all enemies in the game. Features include pathfinding, hp management and movement

    :param target: sprite to chase/harm if spotted.
    :param filename: path to the file used as graphics for the sprite.
    :param position: tuple containing the x and y coordinate to create the sprite at.
    :param max_hp: the max hp for the enemy. Also determines starting hp.
    :param speed: the movement speed for the sprite in px/update.
    :param attack_cooldown: how frequently the enemy can attack.
    :param roaming_dist: the distance to travel, before changing dir, while in roaming state.
    :param scale: the size multiplier for the graphics/hitbox of the sprite.
    """

    def __init__(
            self,
            position: tuple[float, float],
            impassables: arcade.SpriteList,
            window: arcade.Window,
            grid_size: int,
            target_list: arcade.SpriteList,
            filename: str = "images/tiny_dungeon/Tiles/tile_0087.png",
            state: EnemyState=EnemyState.ROAMING,
            max_hp: int = 10,
            speed: int = 1,
            attack_cooldown: int = 1,
            roaming_dist: float = 200,
            scale: float = 1.0):

        super().__init__(
            filename=filename,
            scale=scale,
            center_x=position[0],
            center_y=position[1]
        )

        # hp
        self._max_hp = max_hp
        self._hp = max_hp

        self.window = window
        self.speed = speed
        self.target_list = target_list
        self.target = None
        self.roaming_dist = roaming_dist
        self._state = state

        # attacks
        self.attacks = arcade.SpriteList()
        self.attack_cooldown = attack_cooldown  # the time in seconds between attacking
        self.attack_timer = attack_cooldown  # the timer that we use to track attacking cooldown

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

    @property
    def hp(self):
        return self._max_hp

    @hp.setter
    def hp(self, new_hp):
        self._hp = max(0, min(new_hp, self.max_hp))

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state: EnemyState):
        assert type(new_state) == EnemyState, "state should be an EnemyState"
        self._state = new_state

    def attack(self, width: float, length: float, angle: float, distance: float, duration: float, damage: int):
        """spawn a harmful object in front of the sprite"""

        # can only have one attack at a time - for now
        if not self.attacks and self.attack_timer >= self.attack_cooldown:

            new_attack = Attack(
                duration=duration,
                damage=damage,
                filename="images/RedBox.png",
                image_width=width,
                image_height=length,
                scale=self.scale,
                center_x=self.center_x + (math.sin(angle) * distance),
                center_y=self.center_y + (math.cos(angle) * distance)
            )

            self.attacks.append(new_attack)
            self.attack_timer = 0

    def go_to_position(self, target_pos: tuple[int, int]):
        """
        calculates a path to the target pos. Sets the sprite's path to this path.
        If an enemy has a path, it will automatically follow it.
        If no barrier list is given, use the sprites own barriers.
        """

        target_pos = (int(target_pos[0]), int(target_pos[1]))

        # calculate the path. It will be a list of positions(lists)
        self.path = arcade.astar_calculate_path(self.position,
                                                target_pos,
                                                self.barriers,
                                                diagonal_movement=True)

        # reset this because we are at the start of a new path
        self.cur_path_position = 0

    def on_update(self, delta_time: float = 1 / 60):

        # pick a target to go for. Target is the nearest target
        dist_to_nearest = 9999999
        for t in self.target_list:
            if arcade.get_distance_between_sprites(self, t) < dist_to_nearest:
                self.target = t
                dist_to_nearest = arcade.get_distance_between_sprites(self, t)

        # state control
        if arcade.has_line_of_sight(self.position, self.target.position, self.barriers.blocking_sprites):
            self.state = EnemyState.CHASING
        else:
            self.state = EnemyState.ROAMING

        # chasing state
        angle_to_target = arcade.get_angle_radians(self.center_x, self.center_y, self.target.center_x, self.target.center_y)  # we need this later as well
        if self.state == EnemyState.CHASING:
            self.path = []

            self.center_x += math.sin(angle_to_target) * self.speed
            self.center_y += math.cos(angle_to_target) * self.speed

            # DEMO: Showcasing attacks
            self.attack(width=16, length=16, angle=angle_to_target, distance=32, duration=0.5, damage=2)

        # roaming state
        elif self.state == EnemyState.ROAMING:
            if not self.path:

                # reset movement vectors, so we stop when a path is finished
                self.change_x = 0
                self.change_y = 0

                while True:
                    next_pos = (random.randrange(0, self.window.width), random.randrange(0, self.window.height))

                    # if position is too close, find a new one
                    if arcade.get_distance(self.center_x, self.center_y, next_pos[0], next_pos[1]) > self.roaming_dist:
                        self.go_to_position(next_pos)
                        break

            # follow the path, if present
        if self.path:

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

        # remove the sprite if hp is 0 or less
        if self.hp <= 0:
            self.kill()

        # update attacks
        for a in self.attacks:
            a.on_update()
        self.attack_timer += delta_time

    def on_draw(self, draw_attack_hitboxes: bool=False):
        if draw_attack_hitboxes:
            self.attacks.draw_hit_boxes(arcade.color.NEON_GREEN)
        self.draw()

@unique
class PlayerType(IntEnum):
    """
    Player types that map to numbers in filename suffixes
    """
    WIZARD = 7 * 12 + 0
    MAN_01 = 7 * 12 + 1
    BLACKSMITH = 7 * 12 + 2
    VIKING = 7 * 12 + 3
    MAN_02 = 7 * 12 + 4
    KNIGHT_CLOSED_HELMET = 8 * 12 + 0
    KNIGHT_OPEN_HELMET = 8 * 12 + 1
    KNIGHT_NO_HELMET = 8 * 12 + 2
    WOMAN_YOUNGER = 8 * 12 + 3
    WOMAN_OLDER = 8 * 12 + 4


class Player(arcade.Sprite):
    """
    A player
    """

    def __init__(
            self,
            center_x=0,
            center_y=0,
            speed=2,
            scale=1,
            max_hp: int = 10,
            type:Optional[PlayerType]=None,
            key_up=arcade.key.UP,
            key_down=arcade.key.DOWN,
            key_left=arcade.key.LEFT,
            key_right=arcade.key.RIGHT,
            key_attack=arcade.key.SPACE,
            jitter_amount:int=10, # How much to rotate when walking
            jitter_likelihood:float=0.5 # How likely is jittering?
        ):
        """
        Setup new Player object
        """

        # Pass arguments to class arcade.Sprite
        super().__init__(
            center_x=center_x,
            center_y=center_y,
            scale=scale,
        )

        self.speed = speed

        # We need this to scale the Emotes
        self.scale = scale

        # Pick a random type if none is selected
        if type is None:
            type = random.choice(list(PlayerType))

        # Use the integer value of PlayerType and pad with zeros to get a 4 digit value.
        # Load the image twice, with one flipped, so we have left/right facing textures
        self.textures = arcade.load_texture_pair(
            f"images/tiny_dungeon/Tiles/tile_{type:0=4}.png"
            )

        # Set current texture
        self.texture = self.textures[0]

        self._type = type

        # hp
        self._max_hp = max_hp
        self._hp = max_hp

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

        # Save settings for animating the sprite when walking
        self.jitter_amount = jitter_amount
        self.jitter_likelihood = jitter_likelihood

        # Player's attacks will be stored here
        self._attacks = arcade.SpriteList()

        # Player's emotes will be stored here
        self._emotes = arcade.SpriteList()

    def attack(self):
        """
        Perform an attack
        Only a single attack is allowed
        """
        if len(self._attacks) == 0:
            self._attacks.append(
                PlayerShot(
                    center_x=self.center_x,
                    center_y=self.center_y,
                    max_y_pos=self.center_y+10,
                    speed=50,
                    scale=self.scale
                )
            )

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
    def max_hp(self):
        return self._max_hp

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, new_hp):
        self._hp = max(0, min(new_hp, self.max_hp))  # hp should be greater than 0 and not greater than max hp

    @property
    def attacks(self):
        return self._attacks

    @property
    def emotes(self):
        return self._emotes

    @property
    def type(self):
        return self._type

    def on_key_press(self, key, modifiers):
        """
        Track the state of the control keys
        """
        if key == self.key_left:
            self.left_pressed = True
            # Turns the sprite to the left side.
            self.texture = self.textures[1]
            return
        elif key == self.key_right:
            self.right_pressed = True
            # Turns the sprite to the Right side
            self.texture = self.textures[0]
            return
        elif key == self.key_up:
            self.up_pressed = True
        elif key == self.key_down:
            self.down_pressed = True
        elif key == self.key_atttack:
            self.atttack_pressed = True
            self.attack()

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

        # Rotate the sprite a bit when it's moving
        if (self.change_x != 0 or self.change_y != 0) and random.random() <= self.jitter_likelihood:
            self.angle = random.randint(-self.jitter_amount, self.jitter_amount)
        else:
            self.angle = 0

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
            filename="images/tiny_dungeon/Tiles/tile_0107.png",
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


@unique
class Reaction(IntEnum):
    """
    Reaction names that map to Emote graphics
    The values are calculated from image position in sprite sheet
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
            center_x = position[0] + offset_x,
            center_y = position[1] + offset_y,
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