import arcade
from pyglet.math import Vec2

# Import sprites from local file my_sprites.py
from my_sprites import Player, Weapon, WeaponType


def create_players(number_of_players: int, player_keys: list, scale: int = 1):
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
            speed=3,
            window=None,
            equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
            scale=scale,
            key_up=player_keys[i]["up"],
            key_down=player_keys[i]["down"],
            key_left=player_keys[i]["left"],
            key_right=player_keys[i]["right"],
            key_attack=player_keys[i]["attack"],
        )
        # Create Player spritelist
        player_sprite_list.append(p)

    return player_sprite_list

def load_tilemap(
        map_path_template:str,
        map_layer_config:dict,
        level:int, scale: int=1,
        tile_size=16,
        map_width_tiles: int=30,
        map_height_tiles: int=30
):
    # Create a TileMap with walls, objects etc.
    # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)

    # Checks if the next level exists.
    try:
        open(map_path_template.format(level))
    except FileNotFoundError:
        print("Level Cannot Be Loaded, returning to level 0. 🤖")
        level = 0
    else:
        pass

    tilemap = arcade.tilemap.TileMap(
        map_file=map_path_template.format(level),
        use_spatial_hash=True,
        scaling=scale,
        offset=Vec2(0, 0)
    )

    # Make sure the map we load is as expected
    assert tilemap.tile_width == tile_size, f"Width of tiles in map is {tilemap.tile_width}, it should be {tile_size}."
    assert tilemap.tile_height == tile_size, f"Height of tiles in map is {tilemap.tile_height}, it should be {tile_size}."
    assert tilemap.width == map_width_tiles, f"Width of map is {tilemap.width}, it should be {map_width_tiles}."
    assert tilemap.height == map_height_tiles, f"Height of map is {tilemap.width}, it should be {map_height_tiles}."
    for layer_name in map_layer_config.keys():
        assert layer_name in tilemap.sprite_lists.keys(), f"Layer name '{layer_name}' not in tilemap."

    # Ensure that no tile on the background layer collides with the impassibles layer
    # We want to be able to spawn enemies on the backgrounds layer, so we must ensure
    # that the spawn point is not impassable
    for background_tile in tilemap.sprite_lists["background"]:
        colliding_tiles = background_tile.collides_with_list(tilemap.sprite_lists["impassable"])
        assert len(
            colliding_tiles) == 0, f"A tile on layer 'background' collides with a tile on layer 'impassable' at position {background_tile.position}"

    # Add variable 'seen' to all tiles that has player line of sight. This will be used later on.
    for layer_name in map_layer_config.keys():
        if map_layer_config[layer_name].get("line_of_sight", False):
            for s in tilemap.sprite_lists[layer_name]:
                # Tiles are unseen by default
                s.seen = False

    return tilemap