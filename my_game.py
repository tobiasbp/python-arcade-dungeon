"""
Simple program to show moving a sprite with the keyboard.

This program uses the Arcade library found at http://arcade.academy

Artwork from https://kenney.nl/assets/space-shooter-redux

"""

import arcade

from my_sprites import Player

SPRITE_SCALING = 0.5

# Set the size of the screen
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Variables controlling the player
PLAYER_LIVES = 3
PLAYER_SPEED_X = 5
PLAYER_START_X = SCREEN_WIDTH / 2
PLAYER_START_Y = 50
PLAYER_SHOT_SPEED = 4

FIRE_KEY = arcade.key.SPACE


class PlayerShot(arcade.Sprite):
    """
    A shot fired by the Player
    """

    def __init__(self, start_position, start_angle=90):
        """
        Setup new PlayerShot object
        """

        # Set the graphics to use for the sprite
        # We need to flip it so it matches the mathematical angle/direction
        super().__init__(
            filename="images/Lasers/laserBlue01.png",
            scale=SPRITE_SCALING,
            flipped_diagonally=True,
            flipped_horizontally=True,
            flipped_vertically=False,
        )

        # Shoot points in this direction
        self.angle = start_angle

        # Shoot spawns/starts here
        self.position = start_position

        # Shot moves forward
        self.forward(PLAYER_SHOT_SPEED)

    def update(self):
        """
        Move the sprite
        """

        # Update the position
        self.center_x += self.change_x
        self.center_y += self.change_y

        # Remove shot when over top of screen
        if self.bottom > SCREEN_HEIGHT:
            self.kill()


class GameView(arcade.View):
    """
    The view with the game itself
    """

    def on_show_view(self):
        """
        This is run once when we switch to this view
        """

        # Variable that will hold a list of shots fired by the player
        self.player_shot_list = None

        # Set up the player info
        self.player = None
        self.player_score = None
        self.player_lives = None

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False

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
        arcade.set_background_color(arcade.color.AMAZON)

        self.setup()

    def setup(self):
        """Set up the game and initialize the variables."""

        # No points when the game starts
        self.player_score = 0

        # No of lives
        self.player_lives = PLAYER_LIVES

        # A list of the shots fired by the player
        self.player_shot_list = arcade.SpriteList()

        # Create a Player object
        self.player = Player(
            center_x=PLAYER_START_X,
            center_y=PLAYER_START_Y,
            min_x_pos=0,
            max_x_pos=SCREEN_WIDTH,
            scale=SPRITE_SCALING,
        )

    def on_draw(self):
        """
        Render the screen.
        """

        # Clear screen so we can draw new stuff
        self.clear()

        # Draw the player shot
        self.player_shot_list.draw()

        # Draw the player sprite
        self.player.draw()

        # Draw players score on screen
        arcade.draw_text(
            "SCORE: {}".format(self.player.score),  # Text to show
            10,  # X position
            SCREEN_HEIGHT - 20,  # Y positon
            arcade.color.WHITE,  # Color of text
        )

    def on_update(self, delta_time):
        """
        Movement and game logic
        """

        # Calculate player speed based on the keys pressed
        self.player.change_x = 0

        # Move player with keyboard
        if self.left_pressed and not self.right_pressed:
            self.player.change_x = -PLAYER_SPEED_X
        elif self.right_pressed and not self.left_pressed:
            self.player.change_x = PLAYER_SPEED_X

        # Move player with joystick if present
        if self.joystick:
            self.player.change_x = round(self.joystick.x) * PLAYER_SPEED_X

        # Update player sprite
        self.player.update()

        # Update the player shots
        self.player_shot_list.update()

        # The game is over when the player scores a 100 points
        if self.player.score >= 100:
            self.game_over()

    def game_over(self):
        """
        Call this when the game is over
        """

        # Create a game over view
        game_over_view = GameOverView()

        # Pass the players score to the game over view
        game_over_view.setup(self.player.score)

        # Change to game over view
        self.window.show_view(game_over_view)

    def on_key_press(self, key, modifiers):
        """
        Called whenever a key is pressed.
        """

        if key == arcade.key.ESCAPE:
            self.game_over()

        # Track state of arrow keys
        if key == arcade.key.UP:
            self.up_pressed = True
        elif key == arcade.key.DOWN:
            self.down_pressed = True
        elif key == arcade.key.LEFT:
            self.left_pressed = True
        elif key == arcade.key.RIGHT:
            self.right_pressed = True

        if key == FIRE_KEY:
            # Player gets points for firing?
            self.player.score += 10

            # Create the new shot
            new_shot = PlayerShot(self.player.position)

            # Add the new shot to the list of shots
            self.player_shot_list.append(new_shot)

    def on_key_release(self, key, modifiers):
        """
        Called whenever a key is released.
        """

        if key == arcade.key.UP:
            self.up_pressed = False
        elif key == arcade.key.DOWN:
            self.down_pressed = False
        elif key == arcade.key.LEFT:
            self.left_pressed = False
        elif key == arcade.key.RIGHT:
            self.right_pressed = False

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
            font_size=50,
            anchor_x="center",
        )

        # Draw more text
        arcade.draw_text(
            "Press any key to start the game",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
            anchor_x="center",
        )

    def on_key_press(self, key: int, modifiers: int):
        """
        Start the game when any key is pressed
        """
        game_view = GameView()
        game_view.setup()
        self.window.show_view(game_view)


class GameOverView(arcade.View):
    """
    View to show when the game is over
    """

    def setup(self, score: int):
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
            anchor_x="center",
        )

        # Draw player's score
        arcade.draw_text(
            f"Your score: {self.score}",
            self.window.width / 2,
            self.window.height / 2 - 75,
            arcade.color.WHITE,
            font_size=20,
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
