import arcade
import math
import random
from typing import List, Optional
from enum import IntEnum, Enum, auto, unique

@unique
class Direction(Enum):
    """
    Directions for players/enemies
    """
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()

@unique
class EnemyState(Enum):
    """
    All possible states for enemies
    """

    ROAMING = auto()
    CHASING = auto()


class Enemy(arcade.Sprite):
    """
    parent class for all enemies in the game. Features include pathfinding, hp management and movement

    :param target: sprite to chase/harm if spotted.
    :param filename: path to the file used as graphics for the sprite.
    :param position: tuple containing the x and y coordinate to create the sprite at.
    :param max_hp: the max hp for the enemy. Also determines starting hp.
    :param speed: the movement speed for the sprite in px/update.
    :param roaming_dist: the distance to travel, before changing dir, while in roaming state.
    :param scale: the size multiplier for the graphics/hitbox of the sprite.
    """

    def __init__(
            self,
            position: tuple[float, float],
            impassables: arcade.SpriteList,
            window: arcade.Window,
            grid_size: int,
            target: arcade.Sprite,  # FIXME: Take multiple targets to support multiplayer
            filename: str = "images/tiny_dungeon/Tiles/tile_0087.png",
            state: EnemyState=EnemyState.ROAMING,
            max_hp: int = 10,
            speed: int = 1,
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
        self.target = target
        self.roaming_dist = roaming_dist
        self._state = state

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

        # Enemies emotes will be stored here
        self._emotes = arcade.SpriteList()

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
        # Checks if the _state is the same as the new_state.
        if self._state is not new_state:
            if new_state == EnemyState.CHASING:
                self.react(Reaction.EXCLAMATION_RED)
            elif new_state == EnemyState.ROAMING:
                self.react(Reaction.HEART_BROKEN)

        self._state = new_state

    @property
    def emotes(self):
        return self._emotes

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

    def on_update(self, delta_time: float = 1 / 60):

        # state control
        if arcade.has_line_of_sight(self.position, self.target.position, self.barriers.blocking_sprites):
            self.state = EnemyState.CHASING
        else:
            self.state = EnemyState.ROAMING

        # chasing state
        if self.state == EnemyState.CHASING:
            self.path = []

            angle_to_target = arcade.get_angle_radians(self.center_x, self.center_y, self.target.center_x, self.target.center_y)

            self.center_x += math.sin(angle_to_target) * self.speed
            self.center_y += math.cos(angle_to_target) * self.speed

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

        self._emotes.on_update(delta_time)

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

        # The direction the Player is facing
        self._direction = Direction.RIGHT

        self._type = type

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

        # The weapons carried by the player
        self._weapons = {}

        # No weapon currently in use
        self._equiped = None

        # Add the default weapon
        self.add_weapon(WeaponType.SWORD_SHORT)

        # Player's attacks will be stored here
        # FIXME: Do we want this when we have weapons?
        self._attacks = arcade.SpriteList()

        # Player's emotes will be stored here
        self._emotes = arcade.SpriteList()


    def attack(self):
        """
        Perform an attack using the equiped weapon
        """
        if self.equiped is not None and self.equiped.is_idle:

            # FIXME: Remove the weapon if it has no attacks left

            success = self.equiped.attack(
                position=self.position,
                direction=self.direction,
            )

            if success:
                self.react(Reaction.ANGRY)
            else:
                self.react(Reaction.SAD)

            return True

        else:
            return False


    def react(self, reaction):
        """
        Add an Emote
        """
        # FIXME: Add a limit on number of emotes allowed
        self._emotes.append(
            Emote(
                reaction=reaction,
                position=self.position,
                scale=self.scale
            )
        )


    @property
    def weapons(self):
        """
        A list of weapon types carried by the player
        """
        return self._weapons.keys()

    @property
    def attacks(self):
        return self._attacks

    @property
    def emotes(self):
        return self._emotes

    @property
    def type(self):
        return self._type

    @property
    def equiped(self):
        return self._equiped

    @property
    def direction(self):
        return self._direction

    def add_weapon(self, type):
        """
        Add a weapon to the player's weapons.
        """

        # If we already have the weapon type,
        # it will be replaced by the new weapon.
        self._weapons[type] = Weapon(type)

        # If no weapon is in use, start using the one that was picked up
        if self.equiped is None:
            self.equip(type)

    def equip(self, type):
        """
        The player will start using this weapon type if available.
        This should probably be all type of objects
        Return value reports success.
        """
        if type in self._weapons.keys():
            self._equiped = self._weapons[type]
            return True

        # Could not equip the weapon type
        return False

    def on_key_press(self, key, modifiers):
        """
        Track the state of the control keys
        """
        if key == self.key_left:
            self.left_pressed = True
            # Turns the sprite to the left side.
            self.texture = self.textures[1]
            self._direction = Direction.LEFT
            return
        elif key == self.key_right:
            self.right_pressed = True
            # Turns the sprite to the Right side
            self.texture = self.textures[0]
            self._direction = Direction.RIGHT
            return
        elif key == self.key_up:
            self.up_pressed = True
            self._direction = Direction.UP
        elif key == self.key_down:
            self.down_pressed = True
            self._direction = Direction.DOWN
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

    def draw_sprites(self, pixelated):
        """
        Draw sprites handles by the Player
        """
        self.emotes.draw(pixelated=pixelated)
        self.attacks.draw(pixelated=pixelated)
        if self.equiped is not None:
            # Only draw active weapons
            if not self.equiped.is_idle:
                self.equiped.draw(pixelated=pixelated)

    def update(self):
        """
        Set Sprite's speed based on key status
        """
        # Assume no keys are held
        self.change_x = 0
        self.change_y = 0

        # Move the equiped item to the player's position
        if self.equiped is not None:
            self.equiped.update()

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


@unique
class Reaction(IntEnum):
    """
    Reaction names that map to Emote graphics
    The values are calculated from image position in sprite sheet
    """
    BLANK = 0
    DOT_ONE = 1
    DOT_TWO = 2
    DOT_THREE = 3
    HEART_BROKEN = 4
    HEART = 5
    HEART_TWO = 6
    EXCLAMATION_BLACK = 7
    EXCLAMATION_RED = 8
    CHAR_QUESTION_MARK = 9
    SLEEP_ONE = 10
    SLEEP_TWO = 11
    LINES_VERT = 12
    HAPPY = 13
    SAD = 14
    ANGRY = 15
    SHARDS_GOLD = 16
    STAR = 17
    SPARKS = 18
    NOTE = 19
    RAINDROP = 20
    RAINDROP_TWO = 21
    AIM_RED = 22
    CHAR_DOLLAR = 23
    CHAR_AT = 24
    ICON_CROSS_RED = 25
    ICON_CIRCLE_BLUE = 26
    LIGHTBULB = 27
    LAUGH = 28
    CROSS_GREY = 29

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
        count=3*10)

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

@unique
class WeaponType(IntEnum):
    """
    Weapon types that map to weapon graphics
    The values are calculated from image position in sprite sheet
    """
    SWORD_SHORT = 9*11+4
    SWORD_LONG = 9*11+5
    SWORD_FALCHION = 9*11+6
    SWORD_DOUBLE_SILVER = 9*11+7
    SWORD_DOUBLE_BRONZE = 9*11+8
    HAMMER = 9*12+6
    AXE_DOUBLE = 9*12+7
    AXE_SINGLE = 9*12+8
    STAFF_PURPLE = 9*13+6
    STAFF_GREEN = 9*13+7
    SPEAR = 9*13+8


class Weapon(arcade.Sprite):
    """
    A weapon of a given type.
    Used with players and enemies when they attack.
    """

    # A list of weapon textures from a sprite sheet
    textures: List[arcade.texture.Texture] = arcade.load_spritesheet(
        file_name = "data/rooms/dungeon/tilemap.png",
        sprite_width=16,
        sprite_height=16,
        columns=12,
        count=12*11,
        margin=1)

    # range: How far from the user of the weapon will it attack
    # strength: How much damage will the weapon inflict?
    # speed: How often can the weapon be used (seconds)
    # max_usage: How many times can the weapon be used?
    data = {
        WeaponType.SWORD_SHORT: {
            # Remember to use scale with this when attacking
            "range": 15,
            "strength": 7,
            "speed": 0.8,
            "max_usage": 10
        },
        WeaponType.SWORD_LONG: {
            # Remember to use scale with this when attacking
            "range": 30,
            "strength": 10,
            "speed": 1.2,
            "max_usage": math.inf
        },
        WeaponType.SWORD_FALCHION: {
            # Remember to use scale with this when attacking
            "range": 35,
            "strength": 15,
            "speed": 3,
            "max_usage": math.inf
        },
        WeaponType.SWORD_DOUBLE_SILVER: {
            # Remember to use scale with this when attacking
            "range": 20,
            "strength": 25,
            "speed": 3.2,
            "max_usage": math.inf
        },
        WeaponType.SWORD_DOUBLE_BRONZE: {
            # Remember to use scale with this when attacking
            "range": 30,
            "strength": 15,
            "speed": 1,
            "max_usage": 15
        },
        WeaponType.AXE_SINGLE: {
            # Remember to use scale with this when attacking
            "range": 20,
            "strength": 25,
            "speed": 3,
            "max_usage": math.inf
        },
        WeaponType.AXE_DOUBLE: {
            # Remember to use scale with this when attacking
            "range": 25,
            "strength": 40,
            "speed": 4.5,
            "max_usage": math.inf
        },
        WeaponType.HAMMER: {
            # Remember to use scale with this when attacking
            "range": 15,
            "strength": 30,
            "speed": 2.5,
            "max_usage": 30
        },
        WeaponType.STAFF_PURPLE: {
            # FIXME: Need a setting for distance weapons!
            "range": 15,
            "strength": 10,
            "speed": 1,
            "max_usage": math.inf
        },
        WeaponType.STAFF_GREEN: {
            # FIXME: Need a setting for distance weapons!
            "range": 15,
            "strength": 15,
            "speed": 1,
            "max_usage": math.inf
        },
        WeaponType.SPEAR: {
            # Remember to use scale with this when attacking
            "range": 40,
            "strength": 20,
            "speed": 1,
            "max_usage": math.inf
        }
    }

    def __init__(self,type: WeaponType,position: tuple[int, int]=(0,0),scale:int=1):

        super().__init__(
            center_x = position[0],
            center_y = position[1],
            scale = scale,
            texture = Weapon.textures[type]
        )

        self._type = type
        self._attacks_left:int = Weapon.data[type]["max_usage"]

        # Time in seconds left until weapon can be used again
        self._time_to_idle = 0.0

    @property
    def is_idle(self):
        """
        If the weapon is idle, it can be used for an attack.
        """
        return self._time_to_idle <= 0.0

    @property
    def range(self):
        return Weapon.data[self._type]["range"]

    @property
    def strength(self):
        return Weapon.data[self._type]["strength"]

    @property
    def speed(self):
        return Weapon.data[self._type]["speed"]

    @property
    def attacks_left(self):
        return self._attacks_left

    def attack(self, position: tuple[int,int], direction):
        """
        Weapon attacks at position
        """
        if self.is_idle:
            if self.attacks_left <= 0:
                return False

            self._attacks_left -= 1
            self.position = position
            self._time_to_idle = self.speed

            # Offset position of attack
            if direction == Direction.LEFT:
                self.center_x -= self.range
            elif direction == Direction.RIGHT:
                self.center_x += self.range
            elif direction == Direction.UP:
                self.center_y += self.range
            elif direction == Direction.DOWN:
                self.center_y -= self.range
            else:
                raise ValueError("Invalid direction:", direction)

            return True

    def update(self):
        if not self.is_idle:
            # FIXME: Just to illustrate an attack
            self.angle += 4

            # Time passes
            self._time_to_idle -= 0.03