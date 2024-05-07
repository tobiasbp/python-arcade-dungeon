import arcade
import math
import random
from typing import List, Optional
from enum import IntEnum, Enum, auto, unique

@unique
class Direction(IntEnum):
    """
    Directions for players/enemies
    """
    UP = 0
    UP_RIGHT = 45
    RIGHT = 90
    RIGHT_DOWN = 135
    DOWN = 180
    DOWN_LEFT = 225
    LEFT = 270
    LEFT_UP = 315

@unique
class EnemyState(Enum):
    """
    All possible states for enemies
    """

    RANDOM_WALK = auto()
    GOING_TO_LAST_KNOWN_PLAYER_POS = auto()
    CHASING_PLAYER = auto()


@unique
class Sound(Enum):
    """
    Sound effects
    """

    KNIFE_SLICE = arcade.load_sound("data/audio/rpg/knifeSlice.ogg")
    MONSTER_GRUNT = arcade.load_sound("data/audio/rpg/monster_grunt.wav")
    MONSTER_SNARL = arcade.load_sound("data/audio/rpg/monster_snarl.wav")
    CREAK = arcade.load_sound("data/audio/rpg/creak1.ogg")
    OPENING_SOUND = arcade.load_sound("data/audio/rpg/opening_sound.wav")

    # Footstep sounds.
    FOOTSTEP_00 = arcade.load_sound("data/audio/rpg/footstep00.ogg")
    FOOTSTEP_01 = arcade.load_sound("data/audio/rpg/footstep01.ogg")
    FOOTSTEP_02 = arcade.load_sound("data/audio/rpg/footstep02.ogg")
    FOOTSTEP_03 = arcade.load_sound("data/audio/rpg/footstep03.ogg")
    FOOTSTEP_04 = arcade.load_sound("data/audio/rpg/footstep04.ogg")
    FOOTSTEP_05 = arcade.load_sound("data/audio/rpg/footstep05.ogg")
    FOOTSTEP_06 = arcade.load_sound("data/audio/rpg/footstep06.ogg")
    FOOTSTEP_07 = arcade.load_sound("data/audio/rpg/footstep07.ogg")
    FOOTSTEP_08 = arcade.load_sound("data/audio/rpg/footstep08.ogg")
    FOOTSTEP_09 = arcade.load_sound("data/audio/rpg/footstep09.ogg")


@unique
class EntityType(IntEnum):
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

@unique
class WeaponType(IntEnum):
    """
    Weapon types that map to weapon graphics
    The values are calculated from image position in sprite sheet, but note
    that these are off by one compared to the tilemap due to zero-indexing
    """

    SWORD_SHORT = 8*12+7 # 103
    SWORD_LONG = 8*12+8 # 104
    SWORD_FALCHION = 8*12+9 # 105
    SWORD_DOUBLE_SILVER = 8*12+10 # 106
    SWORD_DOUBLE_BRONZE = 8*12+11 # 107
    HAMMER = 9*12+9 # 117
    AXE_DOUBLE = 9*12+10 # 118
    AXE_SINGLE = 9*12+11 # 119
    STAFF_PURPLE = 10*12+9 # 129
    STAFF_GREEN = 10*12+10 # 130
    SPEAR = 10*12+11 # 131

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
    # hitbox: the points to use as the sprites hitbox
    # strength: How much damage will the weapon inflict?
    # rate: How often can the weapon be used (seconds)
    # max_usage: How many times can the weapon be used?

    data = {
        WeaponType.AXE_DOUBLE: {
            # Remember to use scale with this when attacking
            "range": 25,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 40,
            "rate": 4.5,
            "max_usage": math.inf
        },
        WeaponType.AXE_SINGLE: {
            # Remember to use scale with this when attacking
            "range": 20,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 25,
            "rate": 3,
            "max_usage": math.inf
        },
        WeaponType.HAMMER: {
            # Remember to use scale with this when attacking
            "range": 15,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 30,
            "rate": 2.5,
            "max_usage": 30
        },
        WeaponType.SPEAR: {
            # Remember to use scale with this when attacking
            "range": 40,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 20,
            "rate": 1,
            "max_usage": math.inf
        },
        WeaponType.STAFF_GREEN: {
            # Need a setting for distance weapons!
            "range": 15,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 15,
            "rate": 1,
            "max_usage": math.inf
        },
        WeaponType.STAFF_PURPLE: {
            "range": 15,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 10,
            "rate": 1,
            "max_usage": math.inf
        },
        WeaponType.SWORD_DOUBLE_BRONZE: {
            # Remember to use scale with this when attacking
            "range": 30,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 15,
            "rate": 1,
            "max_usage": 15
        },
        WeaponType.SWORD_DOUBLE_SILVER: {
            # Remember to use scale with this when attacking
            "range": 20,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 25,
            "rate": 3.2,
            "max_usage": math.inf
        },
        WeaponType.SWORD_FALCHION: {
            # Remember to use scale with this when attacking
            "range": 35,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 15,
            "rate": 3,
            "max_usage": math.inf
        },
        WeaponType.SWORD_LONG: {
            # Remember to use scale with this when attacking
            "range": 30,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 10,
            "rate": 1.2,
            "max_usage": math.inf
        },
        WeaponType.SWORD_SHORT: {
            # Remember to use scale with this when attacking
            "range": 15,
            "hit_box": [(10, 10), (10, -10), (-10, -10), (-10, 10)],
            "strength": 7,
            "rate": 0.8,
            "max_usage": 10
        }
    }

    def __init__(self,type: WeaponType,position: tuple[int, int]=(0,0),scale:int=1):

        super().__init__(
            center_x = position[0],
            center_y = position[1],
            scale = scale,
            texture = Weapon.textures[type],
            hit_box_algorithm=None
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
    def type(self):
        return self._type

    @property
    def range(self):
        return Weapon.data[self.type]["range"]

    @property
    def strength(self):
        return Weapon.data[self.type]["strength"]

    @property
    def rate(self):
        return Weapon.data[self._type]["rate"]

    @property
    def attacks_left(self):
        return self._attacks_left

    def attack(self, position: tuple[int,int], angle):
        """
        Weapon attacks at position
        """

        # FIXME: Make resizable hitboxes work for all angles

        self.hit_box = Weapon.data[self.type]["hit_box"]
        if self.is_idle:
            if self.attacks_left <= 0:
                self.kill()
                return False

            self._attacks_left -= 1
            self.position = position
            self._time_to_idle = self.rate

            distance = Weapon.data[self.type]["range"]

            self.center_x = position[0] + (math.sin(angle) * distance)
            self.center_y = position[1] + (math.cos(angle) * distance)

            self._time_to_idle = Weapon.data[self.type]["rate"]
            return True

    def update(self):
        if not self.is_idle:
            # FIXME: Just to illustrate an attack
            self.angle += 4

            # Time passes
            self._time_to_idle -= 1/60  # we don't want to use on_update, so we just use the default delta time
            

class Entity(arcade.Sprite):
    """
    parent class for both enemies and players. Features include attacks, hp and more.
    """

    def __init__(self,
                 position: tuple[float, float],
                 max_hp: int,
                 speed: int,
                 window: arcade.Window,
                 graphics_type: EntityType=None,
                 equipped_weapon: Weapon=None,
                 scale=1.0
                 ):

        super().__init__(scale=scale,
                         center_x=position[0],
                         center_y=position[1])

        # graphics
        # set a random texture type if no type was passed
        if not graphics_type:
            graphics_type = random.choice([e.value for e in EntityType])

        # Load the image twice, with one flipped, so we have left/right facing textures
        self.textures = arcade.load_texture_pair(f"images/tiny_dungeon/Tiles/tile_{graphics_type:0=4}.png")
        self.texture = self.textures[0]

        # hp
        self._max_hp = max_hp
        self._hp = max_hp
        self._health_bar = HealthBar(max_health=max_hp)

        self.speed = speed
        self.window = window

        self._weapons = {}
        self._equipped_weapon = equipped_weapon
        # angle used for the dir the sprite is facing. for the enemy this will usually be the angle to the target
        self._direction = 0  # direction facing. Should be in degrees

        self._emotes = arcade.SpriteList()

        # amount of seconds before the sprite can update
        self.pause_timer = 0

    @property
    def max_hp(self):
        return self._max_hp

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, new_hp):
        self._hp = max(0, min(new_hp, self.max_hp))

    @property
    def equipped_weapon(self):
        return self._equipped_weapon

    @property
    def health_bar(self):
        """
        property that allows the health bar to be drawn from outside
        """
        return self._health_bar

    @property
    def weapons(self):
        return self._weapons.keys()

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

    def add_weapon(self, weapon: Weapon):
        """
        add a weapon to inventory
        """

        # you can only have one of each weapon type in inventory
        self._weapons[weapon.type] = weapon
        self.equip(weapon)

    def equip(self, weapon: Weapon):
        """
        move a weapon from inventory to held slot
        """

        assert weapon in self._weapons.values(), "Requested weapon type is not in inventory"
        self._equipped_weapon = weapon
        self._weapons.pop(weapon.type)

    def attack(self, angle: float):
        """
        Perform an attack using the equiped weapon
        """
        if self.equipped_weapon is not None and self.equipped_weapon.is_idle:

            # FIXME: Remove the weapon if it has no attacks left

            success = self.equipped_weapon.attack(
                position=self.position,
                angle=angle,
            )

            arcade.play_sound(Sound.KNIFE_SLICE.value)

            if success:
                self.react(Reaction.ANGRY)
            else:
                self.react(Reaction.SAD)

            return True

        else:
            return False

    def draw_sprites(self, draw_hitbox: bool=False, draw_attack_hitboxes: bool=False, pixelated: bool=True):
        """
        draw related sprites (emotes and attacks)
        """

        self._emotes.draw(pixelated=pixelated)

        if draw_hitbox:
            self.draw_hit_box(arcade.color.NEON_GREEN, line_thickness=2)

        if self.equipped_weapon is not None:
            if draw_attack_hitboxes:
                self.equipped_weapon.draw_hit_box(arcade.color.NEON_GREEN, line_thickness=2)
            if not self.equipped_weapon.is_idle:
                self.equipped_weapon.draw()

    def update(self):

        if self.pause_timer > 0:
            self.pause_timer -= 1/60  # default value for delta time
            return

        if self.equipped_weapon is not None:
            self.equipped_weapon.update()

            # move the equipped weapon to our position
            self.equipped_weapon.center_x = self.center_x + (
                    math.sin(math.radians(self._direction)) * Weapon.data[self.equipped_weapon.type]["range"])
            self.equipped_weapon.center_y = self.center_y + (
                            math.cos(math.radians(self._direction)) * Weapon.data[self.equipped_weapon.type]["range"])

            if self.equipped_weapon.attacks_left <= 0:
                self._equipped_weapon = None

        # update the health bar
        self.health_bar.health = self._hp
        self.health_bar.position = self.position

        # death
        if self.hp <= 0:
            # FIXME: WHAT DO WE DO WHEN WE DIE?
            pass

        self._emotes.update()


class Enemy(Entity):
    """
    parent class for all enemies in the game. Features include pathfinding, hp management and movement

    :param potential_targets_list: list of sprites to chase/harm if spotted.
    :param filename: path to the file used as graphics for the sprite.
    :param position: tuple containing the x and y coordinate to create the sprite at.
    :param max_hp: the max hp for the enemy. Also determines starting hp.
    :param speed: the movement speed for the sprite in px/update.
    :param roaming_dist: the distance to travel, before changing dir, while in RANDOM_WALK state.
    :param scale: the size multiplier for the graphics/hitbox of the sprite.
    """

    def __init__(
            self,
            position: tuple[float, float],
            max_hp: int,
            speed: int,
            window: arcade.Window,
            impassables: arcade.SpriteList,
            grid_size: int,
            potential_targets_list: arcade.SpriteList,
            state: EnemyState=EnemyState.RANDOM_WALK,
            roaming_dist: float = 200,
            graphics_type: EntityType=None,
            equipped_weapon: Weapon=None,
            scale: float=1.0):

        super().__init__(position=position,
                         graphics_type=graphics_type,
                         max_hp=max_hp,
                         speed=speed,
                         window=window,
                         equipped_weapon=equipped_weapon,
                         scale=scale)

        self.potential_targets_list = potential_targets_list  # list of sprites to chase when spotted
        self.cur_target = None
        self.roaming_dist = roaming_dist
        self._state = state

        # pathfinding
        self.path = []
        self.cur_path_position = 0  # which point on the path we are heading for.

        # prevent enemies from loading simultaneously
        self.pause_timer = random.random()

        # create our own map of barriers
        self.barriers = arcade.AStarBarrierList(
            moving_sprite=self,
            blocking_sprites=impassables,
            grid_size=grid_size,
            left=0,
            right=self.window.width,
            bottom=0,
            top=self.window.height
        )

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state: EnemyState):
        assert type(new_state) == EnemyState, "state should be an EnemyState"
        # Checks if the _state is the same as the new_state.
        if self._state is not new_state:
            if new_state == EnemyState.CHASING_PLAYER:
                self.react(Reaction.EXCLAMATION_RED)
            elif new_state == EnemyState.RANDOM_WALK:
                arcade.play_sound(Sound.MONSTER_GRUNT.value)
                self.react(Reaction.HEART_BROKEN)
                arcade.play_sound(Sound.MONSTER_SNARL.value)

        self._state = new_state

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

    def move_along_path(self):
        """
        Move along the current path, if present.
        """

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

    def update(self):

        super().update()


        # state control
        for t in self.potential_targets_list:  # FIXME: Make the enemy go for the closest player (multiplayer scenario only)
            if arcade.has_line_of_sight(t.position, self.position, self.barriers.blocking_sprites, check_resolution=16):
                self.cur_target = t
                self.state = EnemyState.CHASING_PLAYER
            elif self.cur_target is not None:
                self.go_to_position(self.cur_target.position)
                self.cur_target = None
                self.state = EnemyState.GOING_TO_LAST_KNOWN_PLAYER_POS

        # CHASING_PLAYER state
        if self.state == EnemyState.CHASING_PLAYER:
            self.path = []

            angle_to_target = arcade.get_angle_degrees(self.center_x, self.center_y, self.cur_target.center_x, self.cur_target.center_y)
            self._direction = angle_to_target

            self.center_x += math.sin(math.radians(angle_to_target)) * self.speed
            self.center_y += math.cos(math.radians(angle_to_target)) * self.speed

            self.attack(self._direction)

        # GOING_TO_LAST_KNOWN_PLAYER_POS state
        elif self.state == EnemyState.GOING_TO_LAST_KNOWN_PLAYER_POS:
            # if we are currently moving to the last known point of the player, move along that path, else hop to RANDOM_WALK state
            if self.path:
                self.move_along_path()
            else:
                self.state = EnemyState.RANDOM_WALK

        # RANDOM_WALK state
        elif self.state == EnemyState.RANDOM_WALK:
            # if we have a path, follow it, otherwise calculate a path to a random position
            if self.path:
                self.move_along_path()
            else:

                while True:

                    next_pos = (random.randrange(0, self.window.width), random.randrange(0, self.window.height))

                    # if position is too close, find a new one
                    if arcade.get_distance(self.center_x, self.center_y, next_pos[0], next_pos[1]) > self.roaming_dist:
                        self.go_to_position(next_pos)
                        break


class Player(Entity):
    """
    A player
    """

    def __init__(
            self,
            position: tuple[float, float],
            max_hp: int,
            speed: int,
            window: Optional[arcade.Window],
            graphics_type: EntityType=None,
            equipped_weapon: Weapon=None,
            scale=1.0,
            key_up=arcade.key.UP,
            key_down=arcade.key.DOWN,
            key_left=arcade.key.LEFT,
            key_right=arcade.key.RIGHT,
            key_attack=arcade.key.SPACE,
            joystick=None,
            jitter_amount:int=10, # How much to rotate when walking
            jitter_likelihood:float=0.5, # How likely is jittering?
        ):
        """
        Setup new Player object
        """

        super().__init__(position=position,
                         graphics_type=graphics_type,
                         max_hp=max_hp,
                         speed=speed,
                         window=window,
                         equipped_weapon=equipped_weapon,
                         scale=scale)

        # The direction the Player is facing
        self._direction = Direction.RIGHT

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

        # Configure Joystick
        if joystick is not None:

            # Communicate with joystick
            joystick.open()

            # Map joysticks functions to local functions
            joystick.on_joybutton_press = self.on_joybutton_press
            joystick.on_joybutton_release = self.on_joybutton_release
            joystick.on_joyaxis_motion = self.on_joyaxis_motion
            joystick.on_joyhat_motion = self.on_joyhat_motion

        # Save settings for animating the sprite when walking
        self.jitter_amount = jitter_amount
        self.jitter_likelihood = jitter_likelihood

    @property
    def is_walking(self):
        return True in [self.left_pressed, self.up_pressed, self.right_pressed, self.down_pressed]

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
            self.attack(self._direction)

        # diagonal movement
        if self.up_pressed and self.right_pressed:
            self._direction = Direction.UP_RIGHT
        elif self.right_pressed and self.down_pressed:
            self._direction = Direction.RIGHT_DOWN
        elif self.down_pressed and self.left_pressed:
            self._direction = Direction.DOWN_LEFT
        elif self.left_pressed and self.up_pressed:
            self._direction = Direction.LEFT_UP

        # horizontal and vertical movement
        elif self.left_pressed and not self.right_pressed:
            self._direction = Direction.LEFT
        elif self.right_pressed and not self.left_pressed:
            self._direction = Direction.RIGHT
        elif self.up_pressed and not self.down_pressed:
            self._direction = Direction.UP
        elif self.down_pressed and not self.up_pressed:
            self._direction = Direction.DOWN


    def on_key_release(self, key, modifiers):
        """
        Track the state of the control keys
        """
        if key == self.key_left:
            self.left_pressed = False
        if key == self.key_right:
            self.right_pressed = False
        if key == self.key_up:
            self.up_pressed = False
        if key == self.key_down:
            self.down_pressed = False
        if key == self.key_atttack:
            self.atttack_pressed = False

        # diagonal movement
        if self.up_pressed and self.right_pressed:
            self._direction = Direction.UP_RIGHT
        elif self.right_pressed and self.down_pressed:
            self._direction = Direction.RIGHT_DOWN
        elif self.down_pressed and self.left_pressed:
            self._direction = Direction.DOWN_LEFT
        elif self.left_pressed and self.up_pressed:
            self._direction = Direction.LEFT_UP

        # horizontal and vertical movement
        elif self.left_pressed and not self.right_pressed:
            self._direction = Direction.LEFT
        elif self.right_pressed and not self.left_pressed:
            self._direction = Direction.RIGHT
        elif self.up_pressed and not self.down_pressed:
            self._direction = Direction.UP
        elif self.down_pressed and not self.up_pressed:
            self._direction = Direction.DOWN

    def on_joybutton_press(self, joystick, button_no):
        # Any button press is an attack
        self.on_key_press(self.key_atttack, [])

    def on_joybutton_release(self, joystick, button_no):
        self.on_key_release(self.key_atttack, [])

    def on_joyaxis_motion(self, joystick, axis, value):
        # Round value to an integer to correct imprecise values (negative X value is interpreted as -0.007827878233005237)
        value = round(value)
        if axis == "x":
            if value == 1:
                self.on_key_press(self.key_right, [])
                self.on_key_release(self.key_left, [])
            elif value == -1:
                self.on_key_press(self.key_left, [])
                self.on_key_release(self.key_right, [])
            else:
                self.on_key_release(self.key_right, [])
                self.on_key_release(self.key_left, [])

        if axis == "y":
            # y-value is misinterpreted as inverted, and needs to be corrected
            if value == 1:
                self.on_key_press(self.key_down, [])
                self.on_key_release(self.key_up, [])
            elif value == -1:
                self.on_key_press(self.key_up, [])
                self.on_key_release(self.key_down, [])
            else:
                self.on_key_release(self.key_up, [])
                self.on_key_release(self.key_down, [])

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Note: This game is not compatible with Joyhats")

    def update(self):
        """
        Set Sprite's speed based on key status
        """

        super().update()

        if self.is_walking and random.randint(1, 20) == 1:
            s = random.choice([s for s in Sound if s.name.startswith("FOOTSTEP_")])
            arcade.play_sound(s.value)

        # Assume no keys are held
        self.change_x = 0
        self.change_y = 0

        # Update speed based on held keys

        if self.up_pressed or self.right_pressed or self.down_pressed or self.left_pressed:
            self.change_x = math.sin(math.radians(self._direction))
            self.change_y = math.cos(math.radians(self._direction))
            self.change_x *= self.speed
            self.change_y *= self.speed

        # Rotate the sprite a bit when it's moving
        if (self.change_x != 0 or self.change_y != 0) and random.random() <= self.jitter_likelihood:
            self.angle = random.randint(-self.jitter_amount, self.jitter_amount)
        else:
            self.angle = 0


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

    def update(self):

        self.center_x += self.change_x
        self.center_y += self.change_y

        self.time_left -= 1/60  # we don't want to use on_update, so we just use the default delta_time

        if self.enable_fade:
            self.alpha = max(0, 255 * self.time_left/self.lifetime)

        if self.time_left <= 0:
            self.kill()


class HealthBar(arcade.Sprite):

    def __init__(self,  max_health, center_x=0, center_y=0, bar_width=32, bar_height=5, offset=15, scale=1):

        super().__init__(
            center_x=center_x,
            center_y=center_y,
            scale=scale,
        )

        # variable controlling length of fullness of health bar
        self._max_health = max_health
        self._current_health = self._max_health

        self._bar_width = bar_width * scale
        self._bar_height = bar_height * scale

        self._offset = offset # y offset, to offset the bar, so it is not drawn on top of the player


        # static bar behind the dynamic bar

        self._background_bar = arcade.SpriteSolidColor(
            self._bar_width,
            self._bar_height,
            arcade.color.RED
        )

        # bar changing depending on the percentage variable

        self._foreground_bar = arcade.SpriteSolidColor(
            self._bar_width,
            self._bar_height,
            arcade.color.GREEN
        )

    @property
    def max_health(self):
        return self._max_health

    @property
    def health(self):
        """
        Return current health (0 to max health)
        """
        return self._current_health

    @health.setter
    def health(self, new_health):
        """
        Updates health if health is a value over zero and under max_health
        """
        if 0 < new_health < self._max_health:
            self._current_health = new_health

        """
        calculates ratio of current health and max health and multiplies it with max bar width to get new bar width
        """
        self._foreground_bar.width = int((self._current_health / self._max_health) * self._bar_width)

    @property
    def position(self):
        return self.position

    @position.setter
    def position(self, new_position):
        self.center_x = new_position[0]
        self.center_y = new_position[1]

        self._background_bar.position = (self.center_x, self.center_y + self._offset)
        self._foreground_bar.left = self._background_bar.left
        self._foreground_bar.center_y = self.center_y + self._offset

    def draw(self):
        self._background_bar.draw()
        self._foreground_bar.draw()
