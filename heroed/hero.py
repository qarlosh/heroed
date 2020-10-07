"""Utils related to H.E.R.O. game data or information."""

# ROM addresses where the 8 tables with screen data start. Each table is
# 256 bytes long.
# Each of the 256 screens of the game are defined using 8 bytes, one byte
# of each of these 8 tables.
SCREENS_TABLES_ADDRESSES = (
    0x37F6,
    0x38F6,
    0x39F6,
    0x3AF6,
    0x3BF6,
    0x3CF6,
    0x3DF6,
    0x3EF6,
)

# ROM addresses where the 4 messages cycled in the title screen are.
# each message is 32 bytes long. They're not ascii encoded.
TITLE_SCREEN_MESSAGES_ADDRESSES = (
    0x2309,  # H.E.R.O.TM
    0x2329,  # DESIGNED BY JOHN VAN RYZIN
    0x2349,  # ADAPTED BY THE SOFTWORKS
    0x2369,  # COPYRIGHT 1984 ACTIVISION
)

# pointer to 20 bytes of data, one for each level, indicating the initial
# screen offset from the total of 256 screens.
LEVEL_INITIAL_SCREEN_ADDRESS = 0x37CE

# pointer to 20 bytes of data, one for each level, indicating the number of
# screens of each level, besides the initial screen (i.e. level 2 has 4
# screens and value of 3).
LEVEL_SCREEN_COUNT_ADDRESS = 0x37E2

# Some HERO encoded message chars
#   00-1F:  EMPTY, EMPTY, 0-9, EXCLAM, LEVEL, POWER, PRO, LIVES, BOMBS,
#           POWERBAR, LOGO 1-3
#   20-3F:  LOGO 4-6, SQUARE, A-Z, SPACE, PERIOD
#   40-47:  TM, 1984, UPPER SQUARE, LOWER SQUARE
#   48-7F:  EMPTY
MSGCHR_0 = 0x02  # 0 - these 9 digits are yellow
MSGCHR_9 = 0x0B  # 9
MSGCHR_EXCLAM = 0x0C  # !
MSGCHR_LOGO_1 = 0x1D  # =    rainbow, x4 in the logo
MSGCHR_LOGO_2 = 0x1E  # a
MSGCHR_LOGO_3 = 0x1F  # b
MSGCHR_LOGO_4 = 0x20  # c
MSGCHR_LOGO_5 = 0x21  # d
MSGCHR_LOGO_6 = 0x22  # e
MSGCHR_SQUARE = 0x23  # _
MSGCHR_A = 0x24  # A
MSGCHR_Z = 0x3D  # Z
MSGCHR_SPACE = 0x3E  # ' '
MSGCHR_PERIOD = 0x3F  # .
MSGCHR_TM_1 = 0x40  # t
MSGCHR_TM_2 = 0x41  # m
MSGCHR_YEAR_1 = 0x42  # f    these 4 digits are white
MSGCHR_YEAR_9 = 0x43  # g
MSGCHR_YEAR_8 = 0x44  # h
MSGCHR_YEAR_4 = 0x45  # i
MSGCHR_SQU_UP = 0x46  # (no mapped)
MSGCHR_SQU_LO = 0x47  # (no mapped)

ASCII_TO_HERO = [MSGCHR_SPACE] * 128
# Conversion table from ascii chars to HERO encoded message chars
for n, ascii_code in enumerate(range(ord("A"), ord("Z") + 1)):
    ASCII_TO_HERO[ascii_code] = MSGCHR_A + n
for n, ascii_code in enumerate(range(ord("0"), ord("9") + 1)):
    ASCII_TO_HERO[ascii_code] = MSGCHR_0 + n

ASCII_TO_HERO[ord("!")] = MSGCHR_EXCLAM
ASCII_TO_HERO[ord("=")] = MSGCHR_LOGO_1
ASCII_TO_HERO[ord("a")] = MSGCHR_LOGO_2
ASCII_TO_HERO[ord("b")] = MSGCHR_LOGO_3
ASCII_TO_HERO[ord("c")] = MSGCHR_LOGO_4
ASCII_TO_HERO[ord("d")] = MSGCHR_LOGO_5
ASCII_TO_HERO[ord("e")] = MSGCHR_LOGO_6
ASCII_TO_HERO[ord("_")] = MSGCHR_SQUARE
ASCII_TO_HERO[ord(" ")] = MSGCHR_SPACE
ASCII_TO_HERO[ord(".")] = MSGCHR_PERIOD
ASCII_TO_HERO[ord("t")] = MSGCHR_TM_1
ASCII_TO_HERO[ord("m")] = MSGCHR_TM_2
ASCII_TO_HERO[ord("f")] = MSGCHR_YEAR_1
ASCII_TO_HERO[ord("g")] = MSGCHR_YEAR_9
ASCII_TO_HERO[ord("h")] = MSGCHR_YEAR_8
ASCII_TO_HERO[ord("i")] = MSGCHR_YEAR_4

HERO_TO_ASCII = [" "] * 128
for ascii_code, hero_code in enumerate(ASCII_TO_HERO):
    if hero_code != MSGCHR_SPACE:
        HERO_TO_ASCII[hero_code] = chr(ascii_code)

MSG_LOGO = "====abcde"
MSG_TM = "tm"
MSG_1984 = "fghi"
TITLE_SCREEN_MESSAGE_0 = "            H.E.R.O.tm          "

# The 8 data bytes of each screen
BYTE_ENEMY_LOW = 0  # pos.: xxxxxx__  type: ______xx
BYTE_ENEMY_MID = 1  # pos.: xxxxxx__  type: ______xx
BYTE_LANTERN = 2  # pos.: xxxxxx__    ¿?: ______x_  r_ro_l: _______x
BYTE_LATERAL_MID = 3  # terrain: xxxxxxxx
BYTE_LATERAL_LOW = 4  # terrain: xxxxxxxx
BYTE_CENTER_MID = 5  # terrain: xxxxxxxx
BYTE_CENTER_LOW = 6  # terrain: xxxxxxxx
BYTE_WALL = 7  # wall/gaps: xxxxxx__ magma: ______x_  alt_r: _______x

MAGMA_BIT = 0b00000010  # from BYTE_WALL
ALT_RIGHTSIDE_BIT = 0b00000001  # from BYTE_WALL
RIGHT_TO_LEFT_BIT = 0b00000001  # from BYTE_LANTERN

ENEMY_SPIDER = 0
ENEMY_BAT = 1
ENEMY_MOTH = 2
ENEMY_SNAKE = 3

OBJECT_HIDDEN_POS = 36


ORIGINAL_LEVEL_SCREEN_COUNT = (
    2,
    4,
    6,
    8,
    8,
    10,
    12,
    14,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
    16,
)

ORIGINAL_LEVEL_INITIAL_SCREENS = (
    0,
    2,
    6,
    12,
    20,
    28,
    38,
    50,
    64,
    80,
    96,
    112,
    128,
    144,
    160,
    176,
    192,
    208,
    224,
    240,
)


def leftwards_screens():
    """list of screens that the access to the next screen
    by the left side"""
    return (
        # level 5
        21,
        # level 8
        60,
        61,
        62,
        # level 10
        90,
        91,
        92,
        93,
        94,
        # level 12
        122,
        123,
        124,
        125,
        126,
        # level 13
        137,
        138,
        139,
        140,
        141,
        142,
        # level 14
        146,
        # level 15
        171,
        172,
        173,
        174,
        175,
        # level 17
        199,
        202,
        203,
        204,
        205,
        206,
        # level 19
        234,
        235,
        236,
        237,
        238,
    )


def rightwards_screens():
    """list of screens that the access to the next screen is
    by the right side"""
    return (
        # level 7
        48,
        # level 9
        74,
        75,
        76,
        77,
        78,
        # level 11
        106,
        107,
        108,
        109,
        110,
        # level 12
        114,
        119,
        # level 13
        134,
        # level 14
        147,
        151,
        154,
        155,
        156,
        157,
        158,
        # level 16
        177,
        186,
        187,
        188,
        189,
        190,
        # level 18
        209,
        218,
        219,
        220,
        221,
        222,
        # level 20
        250,
        251,
        252,
        253,
        254,
    )


def horizontal_screens():
    """list of screens that the access to the next screen is
    by the left or right sides, and not going under"""
    return sorted(leftwards_screens() + rightwards_screens())


def final_screens(level_initial_screens, level_screen_count):
    return tuple(
        ini + count - 1
        for ini, count in zip(level_initial_screens, level_screen_count)
    )


def get_levelscr_from_absscr(
    screen_number, level_initial_screens, level_screen_count
):
    """
    Returns a tuple with the level and screen numbers as
    seen in the game, from the absolute screen number (0..255).

      levels  1..20
      screens 1..16

    if can't locate the screen in a level, then return (None, None)
    """
    for level, (initial_screen, screen_count) in enumerate(
        zip(level_initial_screens, level_screen_count)
    ):
        if initial_screen <= screen_number < initial_screen + screen_count:
            return (level + 1, screen_number - initial_screen + 1)
    else:
        return (None, None)


def get_level_color(level_number):
    """returns the color for a specified level (1..20).
    Possible values are:
    0   unknown (incorrect level)
    1   yellow
    2   green
    3   blue
    4   grey
    """
    if level_number is None or not (1 <= level_number <= 20):
        return 0
    else:
        return (level_number - 1) % 4
