import random

import arcade
from pyglet.math import Vec2

from my_sprites import Enemy, EntityType, Player, Weapon, WeaponType, EnemyState

# The keys to control player 1 & 2
PLAYER_KEYS = [
    {"up": arcade.key.UP, "down": arcade.key.DOWN, "left": arcade.key.LEFT, "right": arcade.key.RIGHT, "attack": arcade.key.SPACE},
    {"up": arcade.key.W, "down": arcade.key.S, "left": arcade.key.A, "right": arcade.key.D, "attack": arcade.key.TAB},
]

# All layers configured must exist in the map file.
# line_of_sight: Should sprites only be drawn if they are visible to a player?
# draw: Should the sprites on this layer be drawn?. Config layers, like spawn points, should probably not be drawn
# passable: Can players and enemies can move through sprites on this layer?
# Players: Are spawn points, that's why it doesn't need to be drawn.
MAP_LAYER_CONFIG = {
    "background": {"line_of_sight": False, "draw": True, "passable": True},
    "impassable": {"line_of_sight": False, "draw": True, "passable": False},
    "objects-passable": {"line_of_sight": True, "draw": True, "passable": True},
    "objects-impassable": {"line_of_sight": True, "draw": True, "passable": False},
    "pressure-plates": {"line_of_sight": True, "draw": True, "passable": True},
    "weapons": {"line_of_sight": True, "draw": True, "passable": True},
    "players": {"line_of_sight": False, "draw": False, "passable": True},
    "enemies": {"line_of_sight": False, "draw": True, "passable": True},
    "exits": {"line_of_sight": False, "draw": False, "passable": True},
}

class GameState:
    """
    This class keeps track of players, levels (maps) & phyiscs engines.
    It will be sent through arcade views as the game progresses through levels.
    """
    def __init__(self, no_of_players:int, window:arcade.Window, map_width_tiles:int, map_height_tiles:int, player_speed:int=6000, map_no:int=0, scaling:int=1, tile_size:int=16):
        self.scaling = scaling
        self.players = arcade.SpriteList()
        self.enemies = arcade.SpriteList()
        self.tile_size = tile_size
        self.map_no = map_no
        self.map_width_tiles = map_width_tiles
        self.map_height_tiles = map_height_tiles

        self.window = window

        self.physics_engine = None
        self.tilemap = None
        self._level_clear = False

        self._create_players(no_of_players, player_speed)

        self._load_tilemap(self.map_no)
        self._setup_physics_engine()

    @property
    def level_clear(self):
        return self._level_clear

    def next_map(self):
        """
        Load the next map
        """
        self.map_no += 1
        self._load_tilemap(self.map_no)
        self._setup_physics_engine()

    def _load_tilemap(self, map_no:int,):
        """
        Load map 'map_no'. If there is no
        matching map file, map 0 will be loaded.
        """

        map_file_template = map_path_template = "data/rooms/dungeon/room_{}.tmx"

        # Change level to 0 if chosen level does not have a matching level file
        try:
            open(map_path_template.format(map_no))
        except FileNotFoundError:
            print(f"WARNING: No file found for map {map_no}. Loading map 0 instead.")
            map_no = 0
        else:
            pass

        map_file = map_path_template.format(map_no)

        # Create a TileMap with walls, objects etc.
        # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)
        self.tilemap = arcade.tilemap.TileMap(
            map_file=map_file,
            use_spatial_hash=True,
            scaling=self.scaling,
            offset=Vec2(0,0)
        )

        # Add variable 'seen' to all tiles on layers that has setting 'line of sight: True'.
        # These tiles will not be drawn until a player has discovered them (has line of sight)
        # FIXME: Layer config should be added as attributes in the mapfile itself
        for layer_name in MAP_LAYER_CONFIG.keys():
            if MAP_LAYER_CONFIG[layer_name].get("line_of_sight", False):
                for s in self.tilemap.sprite_lists[layer_name]:
                    # Tiles are unseen by default
                    s.seen = False

        print(f"INFO: Loaded map '{map_file}'")

    def _setup_physics_engine(self):
        """
        Based on the currently loaded map:
        Create a new physics engine. Then add map, players and enemies.
        """
        self._level_clear = False

        # Make sure the loaded map is valid
        self._validate_level()

        self.physics_engine = arcade.PymunkPhysicsEngine()

        self.physics_engine.add_collision_handler(
            "enemy",
            "enemy",
            post_handler=handler_enemy_enemy
        )
        self.physics_engine.add_collision_handler(
            "player",
            "exit",
            post_handler=self._handler_player_exit
        )

        # Add players
        self._position_players()
        self._add_players()

        # Add enemies to match number of
        # sprites in the enemies layer of the map
        self._create_enemies(len(self.tilemap.sprite_lists["enemies"]))
        self._position_enemies()
        self._add_enemies()

        # Add impassable tiles to the physics engine
        self.physics_engine.add_sprite_list(
            self.tilemap.sprite_lists["impassable"],
            damping=0,
            collision_type="impassable",
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

        # Add exits to the physics engine
        self.physics_engine.add_sprite_list(
            self.tilemap.sprite_lists["exits"],
            damping=0,
            collision_type="exit",
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

    def _create_enemies(self, no_of_enemies:int):
        """
        Add enemies to the the self.enemies SpriteList.
        """
        self.enemies = arcade.SpriteList()

        for tile in range(no_of_enemies):
            # Create the enemy
            e = Enemy(
                position=(0, 0),
                max_hp=14,
                speed=4500,
                window=self.window,
                graphics_type=EntityType.VIKING,
                impassables=self.tilemap.sprite_lists["impassable"],
                grid_size=int(self.tilemap.tile_width),
                potential_targets_list=self.players,
                equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
                scale=self.scaling
            )

            self.enemies.append(e)

    def _position_enemies(self):
        """
        Position the players on the current maps start positions
        """
        for i in range(len(self.enemies)):
            self.enemies[i].position = (
                self.tilemap.sprite_lists["enemies"][i].center_x,
                self.tilemap.sprite_lists["enemies"][i].center_y
            )

    def _position_players(self):
        """
        Position the players on the current maps start positions
        """
        for i in range(len(self.players)):
            self.players[i].position = (
                self.tilemap.sprite_lists["players"][i].center_x,
                self.tilemap.sprite_lists["players"][i].center_y
            )

    def _add_enemies(self):
        """
        Position the players on the current maps start positions
        """
        self.physics_engine.add_sprite_list(
            self.enemies,
            damping=0,
            collision_type="enemy",
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

    def _add_players(self):
        """
        Position the players on the current maps start positions
        """
        # prevent accumulation of physics engines from past levels, though we only care about the latest one
        for p in self.players:
            p.physics_engines = [self.physics_engine]

        self.physics_engine.add_sprite_list(
            self.players,
            damping=0,
            collision_type="player",
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

    def _create_players(self, no_of_players, player_speed):
        """
        Create the players
        """
        # replace all sprites on layer "players" with actual player objects
        for i in range(no_of_players):
            # Creates a Player object
            p = Player(
                position=(0, 0),
                max_hp=20,  # FIXME: add some kind of config for the player to avoid magic numbers
                speed=player_speed,
                window=None,
                equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
                scale=self.scaling,
                key_up=PLAYER_KEYS[i]["up"],
                key_down=PLAYER_KEYS[i]["down"],
                key_left=PLAYER_KEYS[i]["left"],
                key_right=PLAYER_KEYS[i]["right"],
                key_attack=PLAYER_KEYS[i]["attack"],
            )

            # Add the player to the list
            self.players.append(p)    


    def _validate_level(self):
        """
        Make sure the loaded map has the features needed by the game.
        """
        # Map must have exits
        assert len(self.tilemap.sprite_lists.get("exits", [])) > 0, "Map does not have any sprites on layer 'exits'"

        # Level must have at least as many player spawn points as we have players
        assert len(self.players) <= len(self.tilemap.sprite_lists["players"]), f"Map does not support {len(self.players)}."

        # Make sure the map we load is as expected
        assert self.tilemap.tile_width == self.tile_size, f"Width of tiles in map is {self.tilemap.tile_width}, it should be {self.tile_size}."
        assert self.tilemap.tile_height == self.tile_size, f"Heigh of tiles in map is {self.tilemap.tile_height}, it should be {self.tile_size}."
        assert self.tilemap.width == self.map_width_tiles, f"Width of map is {self.tilemap.width}, it should be {self.map_width_tiles}."
        assert self.tilemap.height == self.map_height_tiles, f"Height of map is {self.tilemap.width}, it should be {self.map_height_tiles}."

        # All layers in config must be in map
        for layer_name in MAP_LAYER_CONFIG.keys():
            assert layer_name in self.tilemap.sprite_lists.keys(), f"Layer name '{layer_name}' not in tilemap."

        # Ensure that no tile on the background layer collides with the impassibles layer
        # We want to be able to spawn enemies on the backgrounds layer, so we must ensure
        # that the spawn point is not impassable
        for background_tile in self.tilemap.sprite_lists["background"]:
            colliding_tiles = background_tile.collides_with_list(self.tilemap.sprite_lists["impassable"])
            assert len(colliding_tiles) == 0, f"A tile on layer 'background' collides with a tile on layer 'impassable' at position {background_tile.position}"

        print("INFO: Level verified")

        return True

    def _handler_player_exit(self, _1, _2, _3 , _4, _5):
        """
        If a player collides with an exit, the level is cleared.
        In a future scenario, the win condition could be based on attributes i the map file.
        """
        self._level_clear = True

def handler_enemy_enemy(enemy1: Enemy, enemy2: Enemy, _arbiter, _space, _data) -> None:
    """
    The physics engine will call this when two enemies collide
    """

    # If enemies are stuck walking into each other, push them apart.
    if enemy1.state == EnemyState.RANDOM_WALK:
        enemy1.physics_engines[-1].apply_force(enemy1, (-2000, -2000))
    if enemy2.state == EnemyState.RANDOM_WALK:
        enemy2.physics_engines[-1].apply_force(enemy2, (2000, 2000))


def Gore(position, amount, speed, lifetime, start_fade, scale):
    """
    Makes Gore and bloody particles.
    """

    textures = [arcade.make_soft_circle_texture(10, arcade.color.RED),
                arcade.make_soft_circle_texture(10, arcade.color.RED_BROWN)]

    e = arcade.Emitter(
        center_xy=position,
        emit_controller=arcade.EmitBurst(amount),
        particle_factory=lambda emitter: arcade.FadeParticle(
            filename_or_texture=random.choice(textures),
            change_xy=arcade.rand_in_circle((0.0, 0.0), speed),
            lifetime=lifetime,
            scale=scale,
            start_alpha=start_fade,
            end_alpha=0
        )
    )
    return e
