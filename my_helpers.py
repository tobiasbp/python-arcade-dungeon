import arcade
from pyglet.math import Vec2

from my_sprites import Enemy, EntityType, Player, Weapon, WeaponType

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

    def __init__(self, no_of_players:int, window:arcade.Window, player_speed:int=6000, map_no:int=0, scaling:int=1):
        self.window = window
        self.scaling = scaling
        self.players = arcade.SpriteList()
        self.enemies = arcade.SpriteList()
        self.tilemap = None
        self.map_no = map_no
        self.physics_engine = arcade.PymunkPhysicsEngine()

        self._create_players(no_of_players, player_speed)

        self._load_tilemap(self.map_no)
        self._setup_physics_engine()
        #self._add_map_layers()
        #self._add_enemies()
        #self._add_players()
        #self._position_players()

    def next_map(self):
        self.map_no += 1

        
        #for e in self.tilemap.sprite_lists["enemies"]:
        #    self.physics_engine.remove_sprite(e)

        self._load_tilemap(self.map_no)
        self._setup_physics_engine()

        # self._add_enemies()
        # self._add_players()
        # self._position_players()
        # self.players[0].position = (30,30)
        
        #self.physics_engine.resync_sprites()

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
        
        # Remove player sprites from current physics engine
        # The player sprites reference the physics engine, so we need to remove.
        for p in self.players:
            try:
                self.physics_engine.remove_sprite(p)
            except KeyError:
                print("Could not remove player from PE")
                pass


        self._position_players()

        self.physics_engine = arcade.PymunkPhysicsEngine()

        self._add_players()

        self._create_enemies(len(self.tilemap.sprite_lists["enemies"]))
        self._position_enemies()
        self.physics_engine.add_sprite_list(
            self.players,
            damping=0,
            collision_type="enemies",
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )
        self._add_enemies()


        # Add impassable tiles to the physics engine
        self.physics_engine.add_sprite_list(
            self.tilemap.sprite_lists["impassable"],
            damping=0,
            collision_type="impassable",
            body_type=arcade.PymunkPhysicsEngine.STATIC,
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

    def _create_enemies(self, no_of_enemies):
        """
        Create as many enemies as there are tiles in the 'enemies' layer in the current tilemap
        """
        self.enemies = arcade.SpriteList()

        for tile in range(no_of_enemies):
            # Create the enemy
            e = Enemy(
                position=(0,0),
                max_hp=5,
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
            collision_type="player",
            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF
        )

    def _add_players(self):
        """
        Position the players on the current maps start positions
        """
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


def validate_level(tilemap:arcade.tilemap,tile_size:int, map_config:dict, map_width:int, map_height:int ) -> bool:
    # Make sure the map we load is as expected
    assert tilemap.tile_width == tile_size, f"Width of tiles in map is {tilemap.tile_width}, it should be {tile_size}."
    assert tilemap.tile_height == tile_size, f"Heigh of tiles in map is {tilemap.tile_height}, it should be {tile_size}."
    assert tilemap.width == map_width, f"Width of map is {tilemap.width}, it should be {map_width}."
    assert tilemap.height == map_height, f"Height of map is {tilemap.width}, it should be {map_height}."
    for layer_name in map_config.keys():
        assert layer_name in tilemap.sprite_lists.keys(), f"Layer name '{layer_name}' not in tilemap."

    # Ensure that no tile on the background layer collides with the impassibles layer
    # We want to be able to spawn enemies on the backgrounds layer, so we must ensure
    # that the spawn point is not impassable
    for background_tile in tilemap.sprite_lists["background"]:
        colliding_tiles = background_tile.collides_with_list(tilemap.sprite_lists["impassable"])
        assert len(colliding_tiles) == 0, f"A tile on layer 'background' collides with a tile on layer 'impassable' at position {background_tile.position}"

    print("INFO: Level verified")

    return True


