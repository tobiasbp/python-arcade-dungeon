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
from my_sprites import Player, Enemy, Reaction, Weapon, WeaponType

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
PLAYER_SPEED = 5
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
MAP_LAYER_CONFIG = {
    "background": {"line_of_sight": False, "draw": True, "passable": True},
    "impassable": {"line_of_sight": False, "draw": True, "passable": False},
    "objects-passable": {"line_of_sight": True, "draw": True, "passable": True},
    "objects-impassable": {"line_of_sight": True, "draw": True, "passable": False},
    "pressure-plates": {"line_of_sight": True, "draw": True, "passable": True},
    "players": {"line_of_sight": False, "draw": True, "passable": True},
    "enemies": {"line_of_sight": False, "draw": True, "passable": True},
    "exits": {"line_of_sight": False, "draw": False, "passable": True},
}


class GameView(arcade.View):
    """
    The view with the game itself
    """
    
    def __init__(self, level):
        
        super(GameView, self).__init__()

        self.level = level
        
        # Create a TileMap with walls, objects etc.
        # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)
        self.tilemap = arcade.tilemap.TileMap(
            map_file=f"data/rooms/dungeon/room_{self.level}.tmx",
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

        self.player_sprite_list = []

        for i in range(NUM_OF_PLAYERS):
            # Creates Player object
            p = Player(
                center_x=self.tilemap.sprite_lists["players"][i].center_x,
                center_y=self.tilemap.sprite_lists["players"][i].center_y,
                scale=SCALING,
                key_up=PLAYER_KEYS[i]["up"],
                key_down=PLAYER_KEYS[i]["down"],
                key_left=PLAYER_KEYS[i]["left"],
                key_right=PLAYER_KEYS[i]["right"],
                key_attack=PLAYER_KEYS[i]["attack"],
            )
            # Create Player spritelist
            self.player_sprite_list.append(p)

        # Assert that all players have a potential spawnpoint
        assert len(self.tilemap.sprite_lists["players"]) >= len(self.player_sprite_list), "Too many players for tilemap"

        # Change all tiles in the 'enemies' layer to Enemies
        for enemy_index, enemy_position in enumerate([ s.position for s in self.tilemap.sprite_lists["enemies"]]):
            # Create the enemy
            e = Enemy(
                position=enemy_position,
                impassables=self.tilemap.sprite_lists["impassable"],
                grid_size=int(self.tilemap.tile_width),
                window=self.window,
                potential_targets_list=self.player_sprite_list,
                equipped_weapon=Weapon(type=WeaponType.SWORD_SHORT),
                scale=SCALING
            )

            # Go to position of random passable tile
            # FIXME: Often, no path will be found. Why is that??
            # e.go_to_position(random.choice(self.tilemap.sprite_lists["background"]).position)
            # Go to the player's position
            e.go_to_position(self.player_sprite_list[0].position)

            # Replace the spawn point with the new enemy
            self.tilemap.sprite_lists["enemies"][enemy_index] = e


        # We need a physics engine for each player since
        # the one we ar eusing can anly handle a single player
        self.physics_engines = []

        # Create a physics engine for each player.
        # Register player and walls with physics engine
        for p in self.player_sprite_list:
            pe = arcade.PhysicsEngineSimple(
                player_sprite=p,
                walls=self.tilemap.sprite_lists["impassable"]
            )
            self.physics_engines.append(pe)

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
            s.on_draw(draw_attack_hitboxes=DEBUG_MODE)

        # Draw the enemy emotes
        for e in self.tilemap.sprite_lists["enemies"]:
            e.emotes.draw()

    def on_update(self, delta_time: float = 1/60):
        """
        Movement and game logic
        """

        # Collisions code - Checks for all players and enemies' weapons. Checks for the collision.
        for p in self.player_sprite_list:
            for e in self.tilemap.sprite_lists["enemies"]:
                if e.equipped is not None:
                    if arcade.check_for_collision(p, e.equipped):
                        # Damages as much as the enemies' weapon strength.
                            p.hp -= e.equipped.strength

            # Checks after collision with the exit layer.
            for e in self.tilemap.sprite_lists["exits"]:
                if arcade.check_for_collision(p, e):
                    print("A player is on an EXIT!")
                    view = LevelFinishView(self.level)
                    self.window.show_view(view)

            # Updates the player_sprite_list.
            p.update()

        # Update the physics engine for each player
        # Return all sprites involved in collissions
        for pe in self.physics_engines:
            colliding_sprites = pe.update()

        # Update the enemies
        self.tilemap.sprite_lists["enemies"].update()

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
        self.gui_play_button = arcade.gui.UITextureButton(
            x=150,
            y=125,
            width=100,
            height=100,
            texture=arcade.load_texture("images/GUI/start_button_unhovered.png"),
            texture_hovered=arcade.load_texture("images/GUI/start_button_hovered.png"),
            scale=button_scaling,
            style=None
        )

        # Adds the play button to the manager.
        self.manager.add(self.gui_play_button)

        # Makes it to when the player presses the play button it starts the game.
        self.gui_play_button.on_click = self.start_game

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
            "Press Space to start!",
            self.window.width / 2,
            110,
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

    def start_game(self, event=None):
        """
        Starts the game.
        """
        self.opening_sound.stop(self.opening_sound_player)
        game_view = GameView(0)
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

    def __init__(self, level, window=None):
        """
        Create a Game Over-view. Pass the final score to display.
        """
        self.level = level
        self.max_level = 1

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
            if self.level+1 > self.max_level:
                game_view = GameView(level=0)
                self.window.show_view(game_view)
            else:
                game_view = GameView(level=self.level+1)
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
