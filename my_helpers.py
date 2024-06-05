import arcade
from pyglet.math import Vec2

from my_sprites import Player, Weapon, WeaponType

# The keys to control player 1 & 2
PLAYER_KEYS = [
    {"up": arcade.key.UP, "down": arcade.key.DOWN, "left": arcade.key.LEFT, "right": arcade.key.RIGHT, "attack": arcade.key.SPACE},
    {"up": arcade.key.W, "down": arcade.key.S, "left": arcade.key.A, "right": arcade.key.D, "attack": arcade.key.TAB},
]


def load_level(level_no: int, scaling:int, level_config: dict) -> arcade.tilemap:
    """
    Load level no 'level_no'. If there is no
    such level file, level 0 will be loaded.
    """
    map_path_template = "data/rooms/dungeon/room_{}.tmx"

    # Change level to 0 if chosen level does not have a matching level file
    try:
        open(map_path_template.format(level_no))
    except FileNotFoundError:
        print(f"WARNING: Level {level_no} could not be loaded. Loading level instead.")
        level_no = 0
    else:
        pass

    map_file = map_path_template.format(level_no)
    # Create a TileMap with walls, objects etc.
    # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)
    tilemap = arcade.tilemap.TileMap(
        map_file=map_file,
        use_spatial_hash=True,
        scaling=scaling,
        offset=Vec2(0,0)
    )

    # Add variable 'seen' to all tiles that has player line of sight. This will be used later on.
    for layer_name in level_config.keys():
        if level_config[layer_name].get("line_of_sight", False):
            for s in tilemap.sprite_lists[layer_name]:
                # Tiles are unseen by default
                s.seen = False
    
    print(f"INFO: Loaded level '{map_file}'")
    
    return tilemap


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


def create_players(number_of_players:int, scaling:int, speed:int=6000) -> arcade.SpriteList:
    """
    Create the players
    """

    player_sprite_list = arcade.SpriteList()

    # replace all sprites on layer "players" with actual player objects
    for i in range(number_of_players):
        # Creates Player object
        p = Player(
            position=(0, 0),
            max_hp=20,  # FIXME: add some kind of config for the player to avoid magic numbers
            speed=speed,
            window=None,
            equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
            scale=scaling,
            key_up=PLAYER_KEYS[i]["up"],
            key_down=PLAYER_KEYS[i]["down"],
            key_left=PLAYER_KEYS[i]["left"],
            key_right=PLAYER_KEYS[i]["right"],
            key_attack=PLAYER_KEYS[i]["attack"],
        )

        # Add the player to te list
        player_sprite_list.append(p)

    return player_sprite_list
