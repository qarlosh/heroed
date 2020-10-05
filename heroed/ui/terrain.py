# encoding=latin-1
"""Draw the terrain of the game screen. These are the main concepts:

screen    Character position in screen, where 2 terminal chars = 1 MSX tile
          (64 columns terminal)
data      Linear bit representantion of terrain. 32 bits are used to
          represent the 24 central MSX tiles. The 4 leftmost and rightmost
          MSX tiles are handled in other way.
bytes     The 4 bytes used to store the data in the ROM.

The middle area and the lower area are represented the same way.
"""
from heroed import hero
from heroed.utils import Point, clamp
from heroed.ui.cursor import Cursor


def data_to_screen_pos(x):
    """
    Returns the position at screen of a data position.
    x       data position, from 0 to 31
    returns screen position, from 8 to 54
    """
    return x * 3 // 2 + 8


def data_to_screen_width(x):
    """
    Returns the width at screen of a data position.
    It can be 1 column or 2 columns.
    x       data position, from 0 to 31
    returns screen columns occupied by given data position: 1 or 2.
    """
    return x % 2 + 1


def bytes_to_data(bytes, reverse_rightside):
    """
    The 2 bytes are mirrored and reversed (screens are simmetrical).
    bytes               2 bytes. 1st byte is "lateral" region, 2nd byte is
                        "central" region.
    reverse_rightside   (bool) if must reverse right side. This is set by the
                        ALT_RIGHTSIDE_BIT, and only used in middle area (not
                        in upper or lower areas).
    returns bytearray with 4 bytes (data).

    NOTE: The "normal" behavior is to mirror the rightside, but if
    reverse_rightside is set, then that is not mirrored.
    """
    if reverse_rightside:
        return bytearray(
            (
                bytes[0],
                int("{:08b}".format(bytes[1])[::-1], 2),  # reverse bits
                bytes[0],
                int("{:08b}".format(bytes[1])[::-1], 2),  # reverse bits
            )
        )
    else:
        return bytearray(
            (
                bytes[0],
                int("{:08b}".format(bytes[1])[::-1], 2),  # reverse bits
                bytes[1],
                int("{:08b}".format(bytes[0])[::-1], 2),  # reverse bits
            )
        )


def data_to_bytes(data):
    """
    data    bytearray with 4 bytes (data). It uses bytes 0 and 2
    returns bytearray with 2 bytes. 1st byte is "lateral" region, 2nd byte
            is "central" region.
    NOTE: It is not necesary to know if reverse_rightside was used, because
    only first 2 bytes of data are used, and these are not affected by
    reverse_rightside.
    """
    return bytearray(
        (
            data[0],
            int("{:08b}".format(data[1])[::-1], 2)
            # data[2]
        )
    )


def invert_data_bit(data, bit, reversed_rightside):
    """
    Invert bit of data. This is automatically mirrored to the other half.
    data                bytearray with 4 bytes (data). It will be modified
    bit                 number of bit (0..31)
    reversed_rightside  if reverse_rightside was set in the data. In this case,
                        right side is offsetted in some specific way.
    """
    # set direct bit and mirrored bit
    if reversed_rightside:
        # the fixed center-right part can't be modified
        if bit in range(16, 20):
            return
        bit = min(bit % 20, 15)
        for b in (bit, min(bit + 20, 31)):
            data[b // 8] = data[b // 8] ^ (0b10000000 >> (b % 8))
    else:
        for b in (bit, 31 - bit):
            data[b // 8] = data[b // 8] ^ (0b10000000 >> (b % 8))


def data_to_screen_str(data, reversed_rightside):
    """
    converts data to a string of 0 and 1, ready to print to screen.
    data                bytearray with 4 bytes (data).
    reversed_rightside  if reverse_rightside was set in the data. In this case,
                        right side is offsetted in some specific way.
    returns string of 64 chars length.
    """
    if reversed_rightside:
        datastr_left = "".join("{:08b}".format(b) for b in data[0:2])
        datastr_right = "".join("{:08b}".format(b) for b in data[2:4])
        s = "11111111%s" % "".join(
            c * data_to_screen_width(pos) for pos, c in enumerate(datastr_left)
        )
        s += "111111%s" % "".join(
            c * data_to_screen_width(pos)
            for pos, c in enumerate(datastr_right)
        )
        s += s[-2:]
        return s
    else:
        datastr = "".join("{:08b}".format(b) for b in data)
        return "11111111%s11111111" % "".join(
            c * data_to_screen_width(pos) for pos, c in enumerate(datastr)
        )


def bytes_to_screen_str(bytes, reverse_rightside=False):
    """
    converts bytes to a string of 0 and 1, ready to print to screen.
    bytes               2 bytes
    reverse_rightside   see bytes_to_data()
    returns string of 64 chars length.
    """
    return data_to_screen_str(
        bytes_to_data(bytes, reverse_rightside), reverse_rightside
    )


class TerrainCursor(Cursor):
    def __init__(self):
        # (Point) Current cursor position. x is in "data" coords, y is 0 for
        # middle area, 1 for lower area. and 2 for attributes bar below
        self._previous_cursor = None
        self._cursor = Point(0, 0)

    def handle(self, keystroke, screen_data):
        self._previous_cursor = self._cursor
        if keystroke.code == 259:  # KEY_UP
            self._cursor.y = clamp(self._cursor.y - 1, 0, 2)

        elif keystroke.code == 258:  # KEY_DOWN
            self._cursor.y = clamp(self._cursor.y + 1, 0, 2)

        elif keystroke.code == 260:  # KEY_LEFT
            self._cursor.x = clamp(self._cursor.x - 1, 0, 31)

        elif keystroke.code == 261:  # KEY_RIGHT
            self._cursor.x = clamp(self._cursor.x + 1, 0, 31)

        elif keystroke == " ":  # SPACE
            if not self.is_in_attributes():
                if self._cursor.y == 0:
                    LATERAL = hero.BYTE_LATERAL_MID
                    CENTER = hero.BYTE_CENTER_MID
                elif self._cursor.y == 1:
                    LATERAL = hero.BYTE_LATERAL_LOW
                    CENTER = hero.BYTE_CENTER_LOW
                new_screen_data = screen_data.copy()

                # handle ALT_RIGHTSIDE_BIT correctly (only middle area)
                alt_rightside = (
                    bool(screen_data[hero.BYTE_WALL] & hero.ALT_RIGHTSIDE_BIT)
                    and self._cursor.y == 0
                )

                data = bytes_to_data(
                    new_screen_data[LATERAL : CENTER + 1 : 2], alt_rightside
                )
                invert_data_bit(data, self._cursor.x, alt_rightside)
                (
                    new_screen_data[LATERAL],
                    new_screen_data[CENTER],
                ) = data_to_bytes(data)
                return new_screen_data

        return screen_data

    def is_in_attributes(self):
        return self._cursor.y == 2

    def exit_attributes(self):
        self._cursor.y = 1

    def enter_attributes(self):
        self._cursor.y = 2
