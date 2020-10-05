# encoding=latin-1
"""Draw the objects of the game screen. These are the main concepts:

screen    Object position in screen, where 2 terminal chars = 1 MSX tile
          (64 columns terminal)
data      Representantion of object position (0..39)
byte      The byte used to store the data in the ROM

The middle area and the lower area are represented the same way.
"""
from heroed.utils import clamp
import heroed.hero
from heroed.ui.cursor import Cursor

_IN_ATTRIBUTES = 0xFF
_cursor_values = (
    heroed.hero.BYTE_LANTERN,
    heroed.hero.BYTE_WALL,
    heroed.hero.BYTE_ENEMY_MID,
    heroed.hero.BYTE_ENEMY_LOW,
    _IN_ATTRIBUTES,
)


def position_to_screen_pos(x):
    """
    Returns the position at screen of an object data position.
    x       data position, from 0 to 39
    returns screen position, from 2 to 60
    """
    return x * 3 // 2 + 2


def byte_to_position(byte):
    """
    byte   1 byte, with the object position in the 6 most-significant bits
    returns int with object position data (0..39)
    """
    return byte >> 2


def position_to_byte(x):
    """
    x       data position, from 0 to 39
    returns 1 byte, with the object position in the 6 most-significant bits
    """
    return x << 2


def enemy_type_to_byte(enemy_type):
    """
    enemy type  from 0 to 3 (hero.ENEMY_SPIDER..hero.ENEMY_SNAKE)
    returns 1 byte, with the enemy type in the 2 least-significant bits

    """
    return 0b00000011 & enemy_type


def byte_to_screen_pos(byte):
    """
    Returns the position at screen of an object byte
    byte   1 byte, with the object position in the 6 most-significant bits
    returns screen position, from 2 to 96
    """
    return position_to_screen_pos(byte_to_position(byte))


def byte_to_enemy_type(byte):
    """
    Returns the enemy type an object byte
    byte   1 byte, with the enemy type in the 2 least-significant bits
    returns enemy type, from 0 to 3 (hero.ENEMY_SPIDER..hero.ENEMY_SNAKE)
    """
    return 0b00000011 & byte


class ObjectsCursor(Cursor):
    def __init__(self):
        # This is the object byte: hero.BYTE_LANTERN, hero.BYTE_WALL...
        # or 0xFF to position in the attributes bar below
        self._previous_cursor = None
        self._cursor = _cursor_values[0]

    def _move_object(self, position, movement):
        if self._cursor == hero.BYTE_WALL:
            position += movement
            if position == 1:
                return 4
            elif position == -1:
                return 35
            elif position < 4 or position > 35:
                return 0
            return position
        else:
            position += movement
            if position == 37:
                position = 4
            elif position < 4 or position > 35:
                return 36
            return position

    def handle(self, keystroke, screen_data):
        self._previous_cursor = self._cursor
        if keystroke.code == 259:  # KEY_UP
            i = _cursor_values.index(self._cursor) - 1
            self._cursor = _cursor_values[clamp(i, 0, 4)]

        elif keystroke.code == 258:  # KEY_DOWN
            i = _cursor_values.index(self._cursor) + 1
            self._cursor = _cursor_values[clamp(i, 0, 4)]

        elif keystroke.code == 260:  # KEY_LEFT
            if not self.is_in_attributes():
                enemy_type = byte_to_enemy_type(screen_data[self._cursor])
                new_screen_data = screen_data.copy()
                position = byte_to_position(new_screen_data[self._cursor])
                position = self._move_object(position, -1)
                new_screen_data[self._cursor] = position_to_byte(
                    position
                ) | enemy_type_to_byte(enemy_type)
                return new_screen_data

        elif keystroke.code == 261:  # KEY_RIGHT
            if not self.is_in_attributes():
                enemy_type = byte_to_enemy_type(screen_data[self._cursor])
                new_screen_data = screen_data.copy()
                position = byte_to_position(new_screen_data[self._cursor])
                position = self._move_object(position, +1)
                new_screen_data[self._cursor] = position_to_byte(
                    position
                ) | enemy_type_to_byte(enemy_type)
                return new_screen_data

        elif keystroke == " ":  # SPACE - change enemy type
            if not self.is_in_attributes() and self._cursor in (
                hero.BYTE_ENEMY_MID,
                hero.BYTE_ENEMY_LOW,
            ):
                enemy_type = byte_to_enemy_type(screen_data[self._cursor])
                position = byte_to_position(screen_data[self._cursor])
                new_screen_data = screen_data.copy()
                enemy_type += 1
                if enemy_type > hero.ENEMY_SNAKE:
                    enemy_type = hero.ENEMY_SPIDER
                new_screen_data[self._cursor] = position_to_byte(
                    position
                ) | enemy_type_to_byte(enemy_type)
                return new_screen_data

        return screen_data

    def is_in_attributes(self):
        return self._cursor == _IN_ATTRIBUTES

    def exit_attributes(self):
        self._cursor = hero.BYTE_ENEMY_LOW

    def enter_attributes(self):
        self._cursor = _IN_ATTRIBUTES

    def to_str(self):
        return {
            hero.BYTE_LANTERN: "   Lantern    ",
            hero.BYTE_WALL: "     Wall     ",
            hero.BYTE_ENEMY_MID: " Middle enemy ",
            hero.BYTE_ENEMY_LOW: " Lower enemy  ",
            _IN_ATTRIBUTES: "              ",
        }[self._cursor]
