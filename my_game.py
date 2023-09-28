"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade
import random
from pyglet.math import Vec2

# Import sprites from local file my_sprites.py
from my_sprites import Player, PlayerShot, Enemy, Emote, Reaction

# Set the scaling of all sprites in the game
SCALING = 1

# Draw bitmaps without smooth interpolation
DRAW_PIXELATED = True

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
PLAYER_LIVES = 3
PLAYER_SPEED = 5
PLAYER_SHOT_SPEED = 300

FIRE_KEY = arcade.key.SPACE

# All layers configured must exist in the map file.
# line_of_sight: Should sprites only be drawn if they are vissible to a player?
# draw: Should the sprites on this layer be drawn?. Config layers, like spawn points, should probably not be drawn
# passable: Can players and enemies can move through sprites on this layer?
MAP_LAYER_CONFIG = {
    "background": {"line_of_sight": False, "draw": True, "passable": True},
    "impassable": {"line_of_sight": False, "draw": True, "passable": False},
    "objects-passable": {"line_of_sight": True, "draw": True, "passable": True},
    "objects-impassable": {"line_of_sight": True, "draw": True, "passable": False},
    "pressure-plates": {"line_of_sight": True, "draw": True, "passable": True},
    "players": {"line_of_sight": False, "draw": True, "passable": True},
    "enemies": {"line_of_sight": False, "draw": True, "passable": True}
}


class GameView(arcade.View):
    """
    The view with the game itself
    """

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Create a TileMap with walls, objects etc.
        # Spatial hashing is good for calculating collisions for static sprites (like the ones in this map)
        self.tilemap = arcade.tilemap.TileMap(
            map_file="data/rooms/dungeon/room_0.tmx",
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

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = arcade.SpriteList()

        # A list of emotes showing character reactions
        self.emotes_list = arcade.SpriteList()

        # Set up the player info
        # FIXME: Move this into the Player class
        self.player_score = 0
        self.player_lives = PLAYER_LIVES

        # Create a Player object
        self.player = Player(
            center_x=self.tilemap.sprite_lists["players"][0].center_x,
            center_y=self.tilemap.sprite_lists["players"][0].center_y,
            scale=SCALING,
        )

        # Add a demo Emote at the player position
        self.emotes_list.append(
            Emote(
                reaction=Reaction.HAPPY,
                position=self.player.position,
                scale=SCALING
            )
        )

        # Change all tiles in the 'enemies' layer to Enemies
        for enemy_index, enemy_position in enumerate([ s.position for s in self.tilemap.sprite_lists["enemies"]]):
            # Create the enemy
            e = Enemy(
                position=enemy_position,
                impassables=self.tilemap.sprite_lists["impassable"],
                grid_size=int(self.tilemap.tile_width),
                window=self.window,
                scale=SCALING
            )

            # Go to position of random passable tile
            # FIXME: Often, no path will be found. Why is that??
            # e.go_to_position(random.choice(self.tilemap.sprite_lists["background"]).position)
            # Go to the player's position
            e.go_to_position(self.player.position)

            # Replace the spawn point with the new enemy
            self.tilemap.sprite_lists["enemies"][enemy_index] = e


        # Register player and walls with physics engine
        # FIXME: The physics engine can only handle a single player. How do we handle multiplayer?
        self.physics_engine =  arcade.PhysicsEngineSimple(
            player_sprite=self.player,
            walls = self.tilemap.sprite_lists["impassable"]
        )


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

        # Draw the the sprite list from the map if configured to be drawn
        for layer_name, layer_sprites in self.tilemap.sprite_lists.items():
            if MAP_LAYER_CONFIG[layer_name].get("draw", True):
                if MAP_LAYER_CONFIG[layer_name].get("line_of_sight", False):
                    # FIXME: Add logic for drawing stuff that should only be drawn if players have line of sight here
                    pass
                else:
                    layer_sprites.draw(pixelated=DRAW_PIXELATED)

        # Draw the player shot
        self.player_shot_list.draw(pixelated=DRAW_PIXELATED)

        # Draw the player sprite
        self.player.draw(pixelated=DRAW_PIXELATED)

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

        # Draw the player shot
        self.player_shot_list.draw(pixelated=DRAW_PIXELATED)

        # Draw the player sprite
        self.player.draw(pixelated=DRAW_PIXELATED)

        self.emotes_list.draw(pixelated=DRAW_PIXELATED)

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        # Set x/y speed for the player based on key states
        self.player.update()

        # Update the emotes
        self.emotes_list.on_update(delta_time)

        # Update the physics engine (including the player)
        # Return all sprites involved in collissions
        colliding_sprites = self.physics_engine.update()

        # Update the enemies
        self.tilemap.sprite_lists["enemies"].on_update()

        # Update the player shots
        self.player_shot_list.on_update(delta_time)

    def game_over(self):
        """
        Call this when the game is over
        """

        # Create a game over view
        game_over_view = GameOverView(score=self.player_score)

        # Change to game over view
        self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        self.player.on_key_press(key, modifiers)

        # End the game if the escape key is pressed
        if key == arcade.key.ESCAPE:
            self.game_over()

        if key == FIRE_KEY:
            # Player gets points for firing?
            self.player_score += 5

            # Create the new shot
            new_shot = PlayerShot(
                center_x=self.player.center_x,
                center_y=self.player.center_y,
                speed=PLAYER_SHOT_SPEED,
                max_y_pos=SCREEN_HEIGHT,
                scale=SCALING,
            )

            # Add the new shot to the list of shots
            self.player_shot_list.append(new_shot)

    def on_key_release(self, key, modifiers):
        self.player.on_key_release(key, modifiers)

    def on_joybutton_press(self, joystick, button_no):
        print("Button pressed:", button_no)
        # Press the fire key
        self.on_key_press(FIRE_KEY, [])

    def on_joybutton_release(self, joystick, button_no):
        print("Button released:", button_no)

    def on_joyaxis_motion(self, joystick, axis, value):
        print("Joystick axis {}, value {}".format(axis, value))

    def on_joyhat_motion(self, joystick, hat_x, hat_y):
        print("Joystick hat ({}, {})".format(hat_x, hat_y))


class IntroView(arcade.View):
    """
    View to show instructions
    """

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Set the background color
        arcade.set_background_color(arcade.csscolor.DARK_SLATE_BLUE)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """
        Draw this view
        """
        self.clear()

        # Draw some text
        arcade.draw_text(
            "Instructions Screen",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=20,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )

        # Draw more text
        arcade.draw_text(
            "Press any key to start the game",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Start the game when any key is pressed
        """
        game_view = GameView()
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    """
    View to show when the game is over
    """

    def __init__(self, score, window=None):
        """
        Create a Gaome Over view. Pass the final score to display.
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

        # Set the background color
        arcade.set_background_color(arcade.csscolor.DARK_GOLDENROD)

        # Reset the viewport, necessary if we have a scrolling game and we need
        # to reset the viewport back to the start so we can see what we draw.
        arcade.set_viewport(0, self.window.width, 0, self.window.height)

    def on_draw(self):
        """
        Draw this view
        """

        self.clear()

        # Draw some text
        arcade.draw_text(
            "Game over!",
            self.window.width / 2,
            self.window.height / 2,
            arcade.color.WHITE,
            font_size=50,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
            bold=True
        )

        # Draw player's score
        arcade.draw_text(
            f"Your score: {self.score}",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
            font_name=MAIN_FONT_NAME,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Return to intro screen when any key is pressed
        """
        intro_view = IntroView()
        self.window.show_view(intro_view)


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
