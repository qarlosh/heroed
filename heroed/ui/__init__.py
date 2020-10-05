import contextlib
from typing import NamedTuple

from blessed import Terminal
from blessed.sequences import Sequence

from heroed import hero
from heroed.utils import Point, clamp
import heroed.ui.terrain
import heroed.ui.objects
import heroed.ui.help
from heroed.ui.screen_drawing import ScreenDraw
from heroed.ui.misc import ACS_CKBOARD, ACS_DIAMOND
from heroed.ui.cursor import Cursor


class Mode(NamedTuple):
    label: str
    color: str
    cursor: Cursor


class AttributesCursor(Cursor):
    def __init__(self, uiobj):
        # (Point) Current cursor position. x is the attribute selected (0..1),
        # y is 1 when focused and 0 when exited
        self._previous_cursor = None
        self._cursor = Point(0, 0)
        self._uiobj = uiobj

    def handle(self, keystroke, screen_data):
        if keystroke.code == 259:  # KEY_UP, exit attributes bar
            self._cursor.y = 0

        elif keystroke.code == 260:  # KEY_LEFT
            self._cursor.x = clamp(self._cursor.x - 1, 0, 3)

        elif keystroke.code == 261:  # KEY_RIGHT
            self._cursor.x = clamp(self._cursor.x + 1, 0, 3)

        elif keystroke == " ":  # SPACE
            new_screen_data = screen_data.copy()
            # toggle magma
            if self._cursor == Point(0, 1):
                self._uiobj.set_attribute_magma(
                    new_screen_data,
                    not self._uiobj.get_attribute_magma(new_screen_data),
                )
            # change side gap
            elif self._cursor == Point(1, 1):
                side_gap = self._uiobj.get_attribute_sidegap(new_screen_data)
                side_gap += 1
                if side_gap == 1:
                    side_gap = 2
                elif side_gap > 3:
                    side_gap = 0
                self._uiobj.set_attribute_sidegap(new_screen_data, side_gap)
            # toggle alt. layout (different simmetry at right half)
            elif self._cursor == Point(2, 1):
                side_gap = self._uiobj.get_attribute_sidegap(new_screen_data)
                if side_gap == 1:
                    side_gap = 0
                else:
                    side_gap = 1
                self._uiobj.set_attribute_sidegap(new_screen_data, side_gap)
            # change attribute "right to left"  get_attribute_righttoleft
            elif self._cursor == Point(3, 1):
                self._uiobj.set_attribute_righttoleft(
                    new_screen_data,
                    not self._uiobj.get_attribute_righttoleft(new_screen_data),
                )
            return new_screen_data

        return screen_data

    def is_in_attributes(self):
        return self._cursor.y == 1

    def exit_attributes(self):
        self._cursor.y = 0

    def enter_attributes(self):
        self._cursor.y = 1


class UI:

    STATUS_TITLE = "HEROED - MSX H.E.R.O. Editor"

    def __init__(self):
        self.term = Terminal()
        # monkey-patching Terminal with acs()
        Terminal.acs = lambda self, s: self.smacs + s + self.rmacs
        if self.term.width < 80 or self.term.height < 24:
            raise Exception(
                "A minimum of 80 columns x 24 rows terminal is required"
            )

        self._attributes_cursor = AttributesCursor(self)
        self.mode_terrain = Mode(
            " TERRAIN ",
            self.term.black_on_green,
            heroed.ui.terrain.TerrainCursor(),
        )

        self.mode_objects = Mode(
            " OBJECTS ",
            self.term.black_on_yellow,
            heroed.ui.objects.ObjectsCursor(),
        )
        self._mode = self.mode_terrain
        self._cursor = self._mode.cursor
        self._screen_data = None
        self._prior_screen_data = None
        self._screen_number = None
        self.screen_number_to_levelscr = tuple(
            map(hero.get_levelscr_from_absscr, range(256))
        )
        self.mod_name = ""
        self.version = ""
        self.show_screen_data = False
        self.screen_draw = ScreenDraw(self)

    @property
    def mode(self):
        return self._mode

    @property
    def terrain_cursor(self):
        return self.mode_terrain.cursor

    @property
    def objects_cursor(self):
        return self.mode_objects.cursor

    @mode.setter
    def mode(self, value):
        self._mode = value
        self._cursor = self._mode.cursor
        self._attributes_cursor.exit_attributes()
        if self._cursor.is_in_attributes():
            self._cursor.exit_attributes()
        self.draw_attributes_bar()
        self.draw_selection_mode()
        self.draw_screen()

    @property
    def screen_number(self):
        return self._screen_number

    @screen_number.setter
    def screen_number(self, value):
        self._screen_number = value
        self.draw_screen_number_info()

    @property
    def prior_screen_data(self):
        return self._prior_screen_data

    @property
    def screen_data(self):
        return self._screen_data

    # fmt: off
    def set_screen_data(self, screen_data, prior_screen_data=None,
                        redraw_screen=True):
        # store current screen data, because UI can use it later to redraw.
        # prior screen is optional.
        self._screen_data = screen_data
        if prior_screen_data:
            self._prior_screen_data = prior_screen_data
        self.draw_screen_data()
        self.draw_attributes_bar()
        if redraw_screen:
            self.draw_screen(draw_upper_area=True)
    # fmt: on

    def get_attribute_magma(self, screen_data):
        """returns True or False depending on magma is active"""
        return bool(screen_data[hero.BYTE_WALL] & hero.MAGMA_BIT)

    def set_attribute_magma(self, screen_data, value):
        """value   True or False to set magma active/inactive"""
        if value:
            screen_data[hero.BYTE_WALL] |= hero.MAGMA_BIT
        else:
            screen_data[hero.BYTE_WALL] &= ~hero.MAGMA_BIT

    def get_attribute_righttoleft(self, screen_data):
        """returns True or False depending on "right to left" is active"""
        return bool(screen_data[hero.BYTE_LANTERN] & hero.RIGHT_TO_LEFT_BIT)

    def set_attribute_righttoleft(self, screen_data, value):
        """value   True or False to set "right to left" active/inactive"""
        if value:
            screen_data[hero.BYTE_LANTERN] |= hero.RIGHT_TO_LEFT_BIT
        else:
            screen_data[hero.BYTE_LANTERN] &= ~hero.RIGHT_TO_LEFT_BIT

    def get_attribute_sidegap(self, screen_data):
        """returns:
        0   no side gap (only wall or nothing) (in horizontal water
            screens, it means both side gaps!)
        1   alternative right side gap (can have wall)
        2   right side gap
        3   left side gap
        """
        wall_pos = heroed.ui.objects.byte_to_position(screen_data[hero.BYTE_WALL])
        alt_rightside = bool(
            screen_data[hero.BYTE_WALL] & hero.ALT_RIGHTSIDE_BIT
        )
        if wall_pos in range(1, 4):
            return 2
        elif wall_pos in range(36, 64):
            return 3
        elif alt_rightside:
            return 1
        else:
            return 0

    def set_attribute_sidegap(self, screen_data, value):
        """value:
        0   no side gap (only wall or nothing) (in horizontal water
            screens, it means both side gaps!)
        1   alternative right side gap (can have wall)
        2   right side gap (no wall)
        3   left side gap (no wall)
        """
        magma_bit = screen_data[hero.BYTE_WALL] & hero.MAGMA_BIT
        wall_pos = heroed.ui.objects.byte_to_position(screen_data[hero.BYTE_WALL])
        if not (4 <= wall_pos <= 35):
            wall_pos = 0
        if value == 0:
            screen_data[hero.BYTE_WALL] = (
                heroed.ui.objects.position_to_byte(wall_pos) | magma_bit
            )
            screen_data[hero.BYTE_WALL] &= ~hero.ALT_RIGHTSIDE_BIT  # to 0
        elif value == 1:
            screen_data[hero.BYTE_WALL] = (
                heroed.ui.objects.position_to_byte(wall_pos) | magma_bit
            )
            screen_data[hero.BYTE_WALL] |= hero.ALT_RIGHTSIDE_BIT  # to 1
        elif value == 2:
            screen_data[hero.BYTE_WALL] = (
                heroed.ui.objects.position_to_byte(1) | magma_bit
            )  # could be 1..3
            screen_data[hero.BYTE_WALL] &= ~hero.ALT_RIGHTSIDE_BIT  # to 0
        elif value == 3:
            screen_data[hero.BYTE_WALL] = (
                heroed.ui.objects.position_to_byte(36) | magma_bit
            )  # could be 36..63
            screen_data[hero.BYTE_WALL] &= ~hero.ALT_RIGHTSIDE_BIT  # to 0

    # Drawing methods

    def clear(self):
        """clear the entire screen"""
        print(self.term.move_xy(0, 0), end="", flush=True)
        for _ in range(self.term.height):
            print(self.term.normal + " " * self.term.width)

    def redraw_all(self):
        """do a full redraw of all the elements of the screen"""
        self.clear()
        self.draw_status()
        self.draw_mod_name()
        self.draw_screen_data()
        self.draw_screen_number_info()
        self.draw_selection_mode()
        self.draw_screen(draw_upper_area=True)
        self.draw_attributes_bar()

    def draw_mod_name(self):
        """Draw the name of the MOD, above the status bar"""
        pos = Point(0, 22)
        with self.term.location(pos.x, pos.y):
            print(
                self.term.normal
                + ("MOD Name: %s" % self.mod_name.strip()).center(80),
                end="",
            )

    def draw_status(self):
        """Draw the status bar at the bottom"""
        pos = Point(0, 23)
        with self.term.location(pos.x, pos.y):
            keys_msg = "MOD{N}ame  {S}ave  {H}elp  {Q}uit".format(
                N=self.term.reverse("N"),
                S=self.term.reverse("S"),
                H=self.term.reverse("H"),
                Q=self.term.reverse("Q"),
            )

            s = UI.STATUS_TITLE + " v" + self.version
            s = (
                " "
                + s
                + " " * (80 - 2 - Sequence(s + keys_msg, self.term).length())
                + keys_msg
                + " "
            )
            print(self.term.white_on_blue(s), end="")

    def draw_screen_data(self):
        """Draws the 8 bytes of data that define the current screen"""
        pos = Point(0 + 4, 21)
        with self.term.location(pos.x, pos.y):
            if self.show_screen_data and self._screen_data:
                print(
                    self.term.black_on_yellow
                    + "|".join(("%02X",) * 8) % tuple(self._screen_data)
                )
            else:
                print(self.term.normal + " " * 23)

    def draw_screen_number_info(self):
        """Draw the level and screen numbers, at top right"""
        pos = Point(65 + 5, 0)
        with self.term.location():
            if self._screen_number is None:
                for i in (0, 2, 3):
                    print(
                        self.term.move_xy(pos.x, pos.y + i)
                        + self.term.normal
                        + "         ",
                        end="",
                    )
                return

            if self._screen_number in hero.initial_screens():
                color = self.term.white_on_blue
            elif self._screen_number in hero.final_screens():
                color = self.term.white_on_red
            else:
                color = self.term.normal
            level, levelscr = self.screen_number_to_levelscr[
                self._screen_number
            ]
            print(
                self.term.move_xy(pos.x, pos.y)
                + self.term.normal
                + "    [%3d]" % self._screen_number,
                end="",
            )
            print(
                self.term.move_xy(pos.x, pos.y + 2)
                + color
                + "LEVEL  %2d" % level,
                end="",
            )
            print(
                self.term.move_xy(pos.x, pos.y + 3)
                + color
                + "SCREEN %2d" % levelscr,
                end="",
            )

    def draw_selection_mode(self):
        """Draw the active selecion mode, at the top center"""
        pos = Point(0 + 30, 0)
        with self.term.location(pos.x, pos.y):
            s = self._mode.color + self._mode.label
            s += self.term.move_x(pos.x + 10) + self.term.normal
            s += self._cursor.to_str()
            print(s, end="")

    def draw_screen(self, draw_upper_area=False):
        """Draw the game screen"""
        if self._screen_data is None:
            return
        self.screen_draw.draw(draw_upper_area)

    def draw_attributes_bar(self):
        pos = Point(0 + 7, 18 + 1)
        if self._screen_number is None:
            print(
                self.term.move_xy(pos.x, pos.y) + self.term.normal + " " * 62,
                end="",
            )
            return

        levelscr = self.screen_number_to_levelscr[self._screen_number][1]
        with self.term.location(0, pos.y):
            # MAGMA
            status = (
                "On  "
                if self.get_attribute_magma(self._screen_data)
                else "Off "
            )
            selection = (
                self.term.reverse
                if self._attributes_cursor.value() == Point(0, 1)
                else self.term.normal
            )
            print(
                self.term.move_x(pos.x)
                + selection
                + self.term.white_on_red(" MAGMA: %s" % status),
                end="",
            )

            # SIDE GAP
            # When level screen is >= 11, then there is water, and the meaning
            # of "no side gap" changes to "both side gaps"!
            if levelscr >= 11:
                status = ("Both  ", "Both  ", "Right ", "Left  ")[
                    self.get_attribute_sidegap(self._screen_data)
                ]
            else:
                status = ("No    ", "No    ", "Right ", "Left  ")[
                    self.get_attribute_sidegap(self._screen_data)
                ]
            selection = (
                self.term.reverse
                if self._attributes_cursor.value() == Point(1, 1)
                else self.term.normal
            )
            print(
                self.term.move_x(pos.x + 12)
                + selection
                + self.term.white_on_green(" SIDE GAP: %s" % status),
                end="",
            )

            # ALT. LAYOUT (ALT RIGHT BIT)
            status = ("No  ", "Yes ", "No  ", "No  ")[
                self.get_attribute_sidegap(self._screen_data)
            ]
            selection = (
                self.term.reverse
                if self._attributes_cursor.value() == Point(2, 1)
                else self.term.normal
            )
            print(
                self.term.move_x(pos.x + 29)
                + selection
                + self.term.white_on_blue(" ALT. LAYOUT: %s" % status),
                end="",
            )

            # RIGHT TO LEFT ATTR (IN LANTERN BYTE)
            status = (
                "<-- "
                if self.get_attribute_righttoleft(self._screen_data)
                else "--> "
            )
            selection = (
                self.term.reverse
                if self._attributes_cursor.value() == Point(3, 1)
                else self.term.normal
            )
            print(
                self.term.move_x(pos.x + 47)
                + selection
                + self.term.white_on_magenta(" DIR.: %s" % status),
                end="",
            )

    ####

    def process_keystroke(self):
        """Process a keystroke and return None if processed, or
        the keystroke if not processed"""
        keystroke = self.term.inkey()

        # TAB - change terrain/object mode
        if keystroke.code == self.term.KEY_TAB:
            if self._mode == self.mode_terrain:
                self.mode = self.mode_objects
            else:
                self.mode = self.mode_terrain
            return None

        # directions and SPACE (cursor handling)
        elif (
            keystroke.code
            in (
                self.term.KEY_UP,
                self.term.KEY_DOWN,
                self.term.KEY_LEFT,
                self.term.KEY_RIGHT,
            )
            or keystroke == " "
        ):
            new_screen_data = self._cursor.handle(keystroke, self._screen_data)
            draw_upper_area = self._lantern_changed(
                self._screen_data, new_screen_data
            )
            if new_screen_data != self._screen_data:
                self.set_screen_data(new_screen_data, redraw_screen=False)

            # manage enter/exit attributes bar
            if (
                not isinstance(self._cursor, AttributesCursor)
                and self._cursor.is_in_attributes()
            ):
                self._cursor = self._attributes_cursor
                self._cursor.enter_attributes()

            elif (
                isinstance(self._cursor, AttributesCursor)
                and not self._cursor.is_in_attributes()
            ):
                self._cursor = self._mode.cursor
                self._cursor.exit_attributes()
                self.draw_screen()

            self.draw_selection_mode()
            self.draw_attributes_bar()
            self.draw_screen(draw_upper_area=draw_upper_area)
            return None

        # TEST EDITS:
        #   LANTERN REMAINING BITS
        elif keystroke.lower() == "z":
            new_screen_data = self._screen_data.copy()
            new_screen_data[hero.BYTE_LANTERN] = (
                new_screen_data[hero.BYTE_LANTERN] ^ 0b00000010
            )
            self.set_screen_data(new_screen_data)
            return None
        elif keystroke.lower() == "x":
            new_screen_data = self._screen_data.copy()
            new_screen_data[hero.BYTE_LANTERN] = (
                new_screen_data[hero.BYTE_LANTERN] ^ 0b00000001
            )
            self.set_screen_data(new_screen_data)
            return None
        #   WALL BYTE: MAGMA BIT
        elif keystroke.lower() == "c":
            new_screen_data = self._screen_data.copy()
            new_screen_data[hero.BYTE_WALL] = (
                new_screen_data[hero.BYTE_WALL] ^ 0b00000010
            )
            self.set_screen_data(new_screen_data)
            return None
        #   WALL BYTE: ALT RIGHT BIT
        elif keystroke.lower() == "v":
            new_screen_data = self._screen_data.copy()
            new_screen_data[hero.BYTE_WALL] = (
                new_screen_data[hero.BYTE_WALL] ^ 0b00000001
            )
            self.set_screen_data(new_screen_data)
            return None
        return keystroke

    def _lantern_changed(self, old_screen_data, new_screen_data):
        # TODO: implement!
        return True

    def information_message(self, message, timeout=2):
        """Show an information message. Waits for timeout or any key press"""
        pos = Point(0, 23)
        message = " %s " % message
        pos.x = 80 - len(message)
        print(
            self.term.move_xy(pos.x, pos.y)
            + self.term.white_on_green
            + message,
            end="",
            flush=True,
        )
        try:
            self.term.inkey(timeout=timeout)
        finally:
            self.draw_status()

    def show_help(self):
        try:
            total = len(heroed.ui.help.draw_help_funcs)
            for num, fn in enumerate(heroed.ui.help.draw_help_funcs):
                self.clear()
                fn(self.term, ver=self.version)
                print(
                    self.term.move_xy(0, 23)
                    + self.term.white_on_blue(
                        "Press Q to return or any key to continue".ljust(
                            80 - 5
                        )
                        + "(%1d/%1d)" % (num + 1, total)
                    ),
                    end="",
                    flush=True,
                )
                k = self.term.inkey()
                if k.lower() == "q":
                    break
        finally:
            self.redraw_all()

    ####

    def confirm_message(self, message):
        """Show a confirmation message (y/N).
        Returns True if Y or False if N.
        """
        pos = Point(0, 23)
        message = " %s (y/N) " % message
        pos.x = 80 - len(message)
        print(
            self.term.move_xy(pos.x, pos.y)
            + self.term.black_on_bright_yellow
            + message,
            end="",
            flush=True,
        )
        try:
            while True:
                k = self.term.inkey()
                if k.lower() == "y":
                    return True
                elif k.code == self.term.KEY_ENTER or k.lower() == "n":
                    return False
        finally:
            self.draw_status()

    def input_quick_string(self, first_char=""):
        """
        read a quick sequence of keys, with timeout
        """
        keys = first_char
        while True:
            k = self.term.inkey(timeout=0.75)
            if k == "" or k.code == self.term.KEY_ENTER:
                return keys  # finish input (timeout or enter)
            elif k.code == self.term.KEY_ESCAPE:
                return ""  # cancel
            else:
                keys += k  # add input

    def input(self, message="?:", default="", max_length=15):
        """
        read a sequence of chars. Ends with enter, cancel with ESC, and
        can erase last char with backspace.
        """
        pos = Point(0, 23)
        pos.x = 80 - len(message) - max_length - 2
        print(
            self.term.move_xy(pos.x, pos.y)
            + self.term.black_on_bright_yellow
            + message
            + " "
            + default
            + " " * (max_length - len(default))
            + " ",
            end="",
            flush=True,
        )
        print(
            self.term.move_left(max_length - len(default) + 1)
            + self.term.normal_cursor,
            end="",
            flush=True,
        )
        try:
            keys = default
            while True:
                k = self.term.inkey()
                if k.code == self.term.KEY_ENTER:
                    return keys  # finish input
                elif k.code == self.term.KEY_ESCAPE:
                    return default # cancel
                elif k.code == self.term.KEY_BACKSPACE:
                    # erase last char
                    if len(keys) > 0:
                        keys = keys[:-1]
                        print(
                            self.term.move_left + " " + self.term.move_left,
                            end="",
                            flush=True,
                        )
                elif not k.is_sequence:
                    if len(keys) < max_length:
                        print(k, end="", flush=True)
                        keys += k  # add input
        finally:
            print(self.term.hide_cursor, end="", flush=True)
            self.draw_status()

    ####

    @contextlib.contextmanager
    def run(self):
        with self.term.fullscreen(), self.term.cbreak(), self.term.hidden_cursor():
            self.redraw_all()
            yield self
            print(self.term.white_on_black)
