"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
import arcade.gui
import random
from pyglet.math import Vec2

# Import sprites from local file my_sprites.py
from my_sprites import Player, Enemy, Reaction, Weapon, WeaponType, EntityType

# Set the scaling of all sprites in the game
SCALING = 1

# Draw bitmaps without smooth interpolation
DRAW_PIXELATED = True

# should we draw hitboxes, and other info relevant when debugging
DEBUG_MODE = True

# Tiles are squares
TILE_SIZE = 16

# Move the map down from the top left corner by this much
# This will create an area on the screen for score etc.
GUI_HEIGHT = 2 * TILE_SIZE * SCALING

MAP_WIDTH_TILES = 30
MAP_HEIGHT_TILES = 30

# Fonts
MAIN_FONT_NAME = "Kenney Pixel"

# Set the size of the screen
SCREEN_WIDTH = MAP_WIDTH_TILES * TILE_SIZE * SCALING
SCREEN_HEIGHT = MAP_HEIGHT_TILES * TILE_SIZE * SCALING + GUI_HEIGHT

# Variables controlling the player
PLAYER_SPEED = 6000
PLAYER_SHOT_SPEED = 300
PLAYER_SIGHT_RANGE = SCREEN_WIDTH/4 # How far can the player see?

# Amount of players
NUM_OF_PLAYERS = 2

FIRE_KEY = arcade.key.SPACE

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


def create_players(number_of_players: int):
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
            speed=PLAYER_SPEED,
            window=None,
            equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
            scale=SCALING,
            key_up=PLAYER_KEYS[i]["up"],
            key_down=PLAYER_KEYS[i]["down"],
            key_left=PLAYER_KEYS[i]["left"],
            key_right=PLAYER_KEYS[i]["right"],
            key_attack=PLAYER_KEYS[i]["attack"],
        )
        # Create Player spritelist
        player_sprite_list.append(p)

    return player_sprite_list


class GameView(arcade.View):
    """
    The view with the game itself
    """
    
    def __init__(self, level, player_sprite_list):
        """
        level: The level number to load
        player_sprite_list: The Players to add to the level
        """

        super(GameView, self).__init__()

        self.level = level
        self.player_sprite_list = player_sprite_list

        # A format string where you can change the variable in the {}.
        map_path_template = "data/rooms/dungeon/room_{}.tmx"

        # Checks if the next level exists.
        try:
            open(map_path_template.format(self.level))
        except FileNotFoundError:
            print("Level Cannot Be Loaded, returning to level 0. 🤖")
            self.level = 0
        else:
            pass

        # Create a TileMap with walls, objects etc.
        # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)
        self.tilemap = arcade.tilemap.TileMap(
            map_file=map_path_template.format(self.level),
            use_spatial_hash=True,
            scaling=SCALING,
            offset=Vec2(0,0)
        )

        # Make sure the map we load is as expected
        assert self.tilemap.tile_width == TILE_SIZE, f"Width of tiles in map is {self.tilemap.tile_width}, it should be {TILE_SIZE}."
        assert self.tilemap.tile_height == TILE_SIZE, f"Heigh of tiles in map is {self.tilemap.tile_height}, it should be {TILE_SIZE}."
        assert self.tilemap.width == MAP_WIDTH_TILES, f"Width of map is {self.tilemap.width}, it should be {MAP_WIDTH_TILES}."
        assert self.tilemap.height == MAP_HEIGHT_TILES, f"Height of map is {self.tilemap.width}, it should be {MAP_HEIGHT_TILES}."
        for layer_name in MAP_LAYER_CONFIG.keys():
            assert layer_name in self.tilemap.sprite_lists.keys(), f"Layer name '{layer_name}' not in tilemap."

        # Ensure that no tile on the background layer collides with the impassibles layer
        # We want to be able to spawn enemies on the backgrounds layer, so we must ensure
        # that the spawn point is not impassable
        for background_tile in self.tilemap.sprite_lists["background"]:
            colliding_tiles = background_tile.collides_with_list(self.tilemap.sprite_lists["impassable"])
            assert len(colliding_tiles) == 0, f"A tile on layer 'background' collides with a tile on layer 'impassable' at position {background_tile.position}"

        # Add variable 'seen' to all tiles that has player line of sight. This will be used later on.
        for layer_name in MAP_LAYER_CONFIG.keys():
            if MAP_LAYER_CONFIG[layer_name].get("line_of_sight", False):
                for s in self.tilemap.sprite_lists[layer_name]:
                    # Tiles are unseen by default
                    s.seen = False

        self.physics_engine = arcade.PymunkPhysicsEngine()


    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Set up the player info
        # FIXME: Move this into the Player class

        # Get list of joysticks and select the first to be given to the player
        joysticks = arcade.get_joysticks()
        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))
            joystick = joysticks[0]
        else:
            print("No joysticks found")
            joystick = None

        self.player_score = 0

        for i in range(len(self.player_sprite_list)):
            self.player_sprite_list[i].position = (
                self.tilemap.sprite_lists["players"][i].center_x,
                self.tilemap.sprite_lists["players"][i].center_y
            )


        # Assert that all players have a potential spawnpoint
        assert len(self.tilemap.sprite_lists["players"]) >= len(self.player_sprite_list), "Too many players for tilemap"

        # Change all tiles in the 'enemies' layer to Enemies
        for enemy_index, enemy_position in enumerate([ s.position for s in self.tilemap.sprite_lists["enemies"]]):
            # Create the enemy
            e = Enemy(
                position=enemy_position,
                max_hp=5,
                speed=4500,
                window=self.window,
                graphics_type=EntityType.VIKING,
                impassables=self.tilemap.sprite_lists["impassable"],
                grid_size=int(self.tilemap.tile_width),
                potential_targets_list=self.player_sprite_list,
                equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
                scale=SCALING
            )

            # Replace the spawn point with the new enemy
            self.tilemap.sprite_lists["enemies"][enemy_index] = e

        # Get list of joysticks
        joysticks = arcade.get_joysticks()

        if joysticks:
            print("Found {} joystick(s)".format(len(joysticks)))

            # Use 1st joystick found
            self.joystick = joysticks[0]

            # Communicate with joystick
            self.joystick.open()

            # Map joysticks functions to local functions
            self.joystick.on_joybutton_press = self.on_joybutton_press
            self.joystick.on_joybutton_release = self.on_joybutton_release
            self.joystick.on_joyaxis_motion = self.on_joyaxis_motion
            self.joystick.on_joyhat_motion = self.on_joyhat_motion

        else:
            print("No joysticks found")
            self.joystick = None

        # add all sprites to physics engine
        self.physics_engine.add_sprite_list(self.player_sprite_list,
                                            damping=0,
                                            collision_type="player",
                                            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF)

        self.physics_engine.add_sprite_list(self.tilemap.sprite_lists["impassable"],
                                            damping=0,
                                            collision_type="impassable",
                                            body_type=arcade.PymunkPhysicsEngine.STATIC,
                                            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF)

        self.physics_engine.add_sprite_list(self.tilemap.sprite_lists["enemies"],
                                            damping=0,
                                            collision_type="enemy",
                                            moment_of_intertia=arcade.PymunkPhysicsEngine.MOMENT_INF)

        # Set the background color
        arcade.set_background_color(arcade.color.BLACK)

    def on_draw(self):
        """
        Render the screen.
        """

        # Clear screen so we can draw new stuff
        self.clear()

        # Draw the sprite list from the map if configured to be drawn
        for layer_name, layer_sprites in self.tilemap.sprite_lists.items():
            if MAP_LAYER_CONFIG[layer_name].get("draw", True):
                if not MAP_LAYER_CONFIG[layer_name].get("line_of_sight", False):
                    # If the layer is not configured as line_of_sight, all tiles will be drawn
                    layer_sprites.draw(pixelated=DRAW_PIXELATED)
                else:
                    # Run through line_of_sight tiles
                    for s in layer_sprites:
                        if s.seen:
                            # If the tile has already been seen, draw it and skip the rest.
                            s.draw(pixelated=DRAW_PIXELATED)
                        else:
                            # If player has line of sight to an unseen tile, it's marked as seen
                            try:
                                if arcade.has_line_of_sight(
                                        point_1 = s.position,
                                        point_2 = self.player_sprite_list[0].position,
                                        walls = self.tilemap.sprite_lists["impassable"],
                                        check_resolution = TILE_SIZE*2,
                                        max_distance = PLAYER_SIGHT_RANGE
                                ):
                                    s.seen = True
                            except ZeroDivisionError:
                                # An error may occur in the has_line_of_sight() function
                                # if the distance between point_1 and point_2 is too close to zero.
                                # In that case we assume that the tile has already been seen.
                                pass

        # Draw players score on screen
        arcade.draw_text(
            f"SCORE: {self.player_score}",  # Text to show
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y positon
            arcade.color.WHITE,  # Color of text
            font_size=TILE_SIZE,
            font_name=MAIN_FONT_NAME,
            bold=True,
        )

        # Draw the player sprite and its objects (weapon & emotes)

        for p in self.player_sprite_list:
            # Draw the player sprite
            # Draw the player sprite and its attacks and emotes
            p.draw(pixelated=DRAW_PIXELATED)
            p.draw_sprites(pixelated=DRAW_PIXELATED)

        for s in self.tilemap.sprite_lists["enemies"]:
            s.draw(pixelated=DRAW_PIXELATED)
            s.draw_sprites(draw_attack_hitboxes=DEBUG_MODE, pixelated=DRAW_PIXELATED)

        for e in self.tilemap.sprite_lists["enemies"]:
            e.health_bar.draw()

        for p in self.player_sprite_list:
            p.health_bar.draw()

    def on_update(self, delta_time: float = 1/60):
        """
        Movement and game logic
        """

        # Check for player collisions
        for p in self.player_sprite_list:
            for e in self.tilemap.sprite_lists["enemies"]:
                # Check if the enemy's weapon has hit the player
                if e.equipped_weapon is not None and e.equipped_weapon.attack_point is not None:
                    if p.collides_with_point(e.equipped_weapon.attack_point):
                        p.hp -= e.equipped_weapon.strength
                        e.equipped_weapon.attack_point = None
                # Check if the player's weapon has hit the enemy
                if p.equipped_weapon is not None and p.equipped_weapon.attack_point is not None:
                    if e.collides_with_point(p.equipped_weapon.attack_point):
                        e.hp -= p.equipped_weapon.strength
                        p.equipped_weapon.attack_point = None

            # Checks after collision with the exit layer.
            for e in self.tilemap.sprite_lists["exits"]:
                if arcade.check_for_collision(p, e):
                    print("A player is on an EXIT!")
                    view = LevelFinishView(self.level, self.player_sprite_list)
                    self.window.show_view(view)

            # Pick up weapons from tilemap if the players are standing on any
            for w in self.tilemap.sprite_lists["weapons"]:
                if arcade.check_for_collision(p, w):
                    # create a weapon type based on the tile id. If the tile is not a weapon, raise an error
                    new_weapon_type = WeaponType(w.properties["tile_id"])
                    p.add_weapon(Weapon(new_weapon_type))

                    # Remove weapon from tilemap, as the player has picked it up
                    w.kill()

            # Updates the player_sprite_list.
            p.update()

        # Update the enemies
        self.tilemap.sprite_lists["enemies"].update()

        self.physics_engine.step()

    def game_over(self):
        """
        Call this when the game is over
        """

        # Create a game over view
        game_over_view = GameOverView(score=self.player_score)

        # Change to game over view
        self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        for p in self.player_sprite_list:
            p.on_key_press(key, modifiers)

        # End the game if the escape key is pressed
        if key == arcade.key.ESCAPE:
            self.game_over()
        elif key == arcade.key.R and DEBUG_MODE:
            # Restarts the game when Debug mode is True and you pressed R.
            game_view = GameView()
            self.window.show_view(game_view)
            print("Game Reset! 🔁 -- Turn Debug mode off to remove this feature! ✔")

    def on_key_release(self, key, modifiers):
        for p in self.player_sprite_list:
            p.on_key_release(key, modifiers)


class IntroView(arcade.View):
    """
    View to show instructions
    """

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        self.opening_sound = arcade.load_sound("data/audio/rpg/opening_sound.wav")
        self.opening_sound_player = self.opening_sound.play()

        # Set the background color
        arcade.set_background_color(arcade.csscolor.SLATE_GREY)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

        button_scaling = 1.6

        # Make the title Sprite
        self.title = arcade.Sprite(
            "images/GUI/title_game_start.png",
            button_scaling*1.5
            )
        self.title.center_x = SCREEN_WIDTH//2
        self.title.center_y = 350

        # Makes the manager that contains the GUI button and enables it to the game.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Makes the play button.
        self.one_player = arcade.gui.UITextureButton(
            x=50,
            y=125,
            width=100,
            height=100,
            texture=arcade.load_texture("images/GUI/button_players_one.png"),
            texture_hovered=arcade.load_texture("images/GUI/button_players_one_chosen.png"),
            scale=button_scaling*2,
            style=None
        )
        # Makes the play button.
        self.two_player = arcade.gui.UITextureButton(
            x=350,
            y=125,
            width=100,
            height=100,
            texture=arcade.load_texture("images/GUI/button_players_two.png"),
            texture_hovered=arcade.load_texture("images/GUI/button_players_two_chosen.png"),
            scale=button_scaling*2,
            style=None
        )

        # Adds the play button to the manager.
        self.manager.add(self.one_player)
        self.manager.add(self.two_player)

        # Makes it to when the player presses the play button it starts the game.
        self.one_player.on_click = self.set_one_player
        self.two_player.on_click = self.set_two_players

    def on_draw(self):
        """
        Draw this view
        """
        self.clear()

        # Draws the title and the manager which has the play button.
        self.title.draw(pixelated=DRAW_PIXELATED)
        self.manager.draw()

        # Info how to also start the game.
        arcade.draw_text(
            "Or press Space to start!",
            self.window.width / 2,
            110,
            arcade.color.BLACK,
            font_size=15,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )
        # Info how to also start the game.
        arcade.draw_text(
            "Press One of the buttons to start!",
            self.window.width / 2,
            210,
            arcade.color.BLACK,
            font_size=15,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Start the game when any key is pressed
        """
        if key == arcade.key.SPACE:
            self.start_game()

    def set_one_player(self, event=None):
        """
        Sets the normal value of players to one.
        """

        self.player_amount = 1
        self.start_game()

    def set_two_players(self, event=None):
        """
        Sets the normal value of players to two.
        """

        self.player_amount = 2
        self.start_game()

    def start_game(self, event=None):
        """
        Starts the game.
        """

        self.player_sprite_list = arcade.SpriteList()

        self.player_sprite_list = create_players(self.player_amount)

        # Prevent the sound from playing after the game starts
        self.opening_sound.stop(self.opening_sound_player)
        print("The amount of Players are:", self.player_amount)
        game_view = GameView(level=0, player_sprite_list=self.player_sprite_list)
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    """
    View to show when the game is over
    """

    def __init__(self, score, window=None):
        """
        Create a Game Over-view. Pass the final score to display.
        """
        self.score = score

        super().__init__(window)

    def setup_old(self, score: int):
        """
        Call this from the game so we can show the score.
        """
        self.score = score

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """
        button_scaling = 1.6

        # Set the background color
        arcade.set_background_color(arcade.csscolor.BLACK)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)


        # Make the title Sprite
        self.title = arcade.Sprite(
            filename="images/GUI/title_game_over.png",
            scale=button_scaling*2,
            center_x=SCREEN_WIDTH//2,
            center_y=350,
            )

        self.subtitle = arcade.Sprite(
            filename=f"images/GUI/end_text_{random.randint(1, 5)}.png",
            scale=button_scaling*2,
            center_x=self.title.center_x,
            center_y=self.title.center_y - 50
            )

        # Makes the manager that contains the GUI button and enables it to the game.
        self.manager = arcade.gui.UIManager()
        self.manager.enable()

        # Makes the play button.
        gui_play_button = arcade.gui.UITextureButton(
            x=150,
            y=125,
            width=100,
            height=100,
            texture=arcade.load_texture("images/GUI/restart_button_unhovered.png"),
            texture_hovered=arcade.load_texture("images/GUI/restart_button_hovered.png"),
            scale=button_scaling,
            style=None
        )

        # Adds the play button to the manager.
        self.manager.add(gui_play_button)

        # Makes it to when the player presses the play button it starts the game.
        gui_play_button.on_click = self.restart

    def on_draw(self):
        """
        Draw this view
        """

        self.clear()

        # Draws the game over title and the under title.
        self.title.draw(pixelated=DRAW_PIXELATED)
        self.subtitle.draw(pixelated=DRAW_PIXELATED)

        # Draws the manager.
        self.manager.draw()

        # Draw player's score.
        arcade.draw_text(
            f"Your score: {self.score}",
            self.window.width / 2,
            self.window.height - 75,
            arcade.color.WHITE,
            font_size=20,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Return to intro screen when any key is pressed.
        """

        if key == arcade.key.SPACE:
            intro_view = IntroView()
            self.window.show_view(intro_view)

    def restart(self, event):
        """
        Return to intro screen when the restart button pressed
        """
        intro_view = IntroView()
        self.window.show_view(intro_view)


class LevelFinishView(arcade.View):
    """
    View to show when the game is over
    """

    def __init__(self, level, player_sprite_list, window=None):
        """
        Create a Game Over-view. Pass the final score to display.
        """
        self.level = level
        self.player_sprite_list = player_sprite_list

        # Set all movements to false so there's no auto-moving when the next level starts.
        for p in player_sprite_list:
            p.all_keys_off()

        super().__init__(window)

    def setup_old(self, score: int):
        """
        Call this from the game so we can show the score.
        """
        pass

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """
        # Set the background color
        arcade.set_background_color(arcade.csscolor.BLACK)

    def on_draw(self):
        """
        Draw this view
        """

        self.clear()

        # Congratulations message!
        arcade.draw_text(
            "You beat the level!",
            self.window.width / 2,
            250,
            arcade.color.TROLLEY_GREY,
            font_size=35,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )

        # Instructions message
        arcade.draw_text(
            "Press SPACE to continue your adventure..",
            self.window.width / 2,
            200,
            arcade.color.TROLLEY_GREY,
            font_size=15,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Return to intro screen when any key is pressed.
        """

        # Remember to add onto the self.max_level everytime a person
        # adds a new level/stage.

        if key == arcade.key.SPACE:
            # Turns to the next level.
            next_level = self.level + 1

            game_view = GameView(level=next_level, player_sprite_list=self.player_sprite_list)
            self.window.show_view(game_view)


def main():
    """
    Main method
    """
    # Create a window to hold views
    window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT)

    # Game starts in the intro view
    start_view = IntroView()

    window.show_view(start_view)

    arcade.run()

if __name__ == "__main__":
    main()
