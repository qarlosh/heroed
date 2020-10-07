from heroed import hero
from heroed.utils import Point
import heroed.ui.terrain
import heroed.ui.objects
from heroed.ui.misc import ACS_CKBOARD, ACS_DIAMOND


class ScreenDraw:
    def __init__(self, uiobj):
        self.uiobj = uiobj
        self.pos = Point(4, 2)
        self._levelscr = None
        self._terrain_color = None

    def draw(self, draw_upper_area=False):
        """Draw the game screen.
        A game screen in HERO is 32x17 chars. Show it using 64x17 chars.
        """
        self.draw_terrain(draw_upper_area)
        self.draw_objects()

    def draw_terrain(self, draw_upper_area=False):
        """Draw the terrain of the screen"""
        level, self._levelscr = hero.get_levelscr_from_absscr(
            self.uiobj.screen_number,
            self.uiobj.level_initial_screens,
            self.uiobj.level_screen_count,
        )

        self._terrain_color = {
            0: self.uiobj.term.yellow_on_black,
            1: self.uiobj.term.green_on_black,
            2: self.uiobj.term.blue_on_black,
            3: self.uiobj.term.white_on_black,
        }[hero.get_level_color(level)]

        if draw_upper_area:
            self.draw_terrain_up_area()
        self.draw_terrain_mid_area()
        self.draw_terrain_lo_area()

    def draw_terrain_up_area(self):
        """Draw the upper area of terrain. This is drawn using prior screen
        data."""
        if self.uiobj.screen_number in self.uiobj.level_initial_screens:
            # initial screens are special cases - upper area is a preset
            row = (
                heroed.ui.terrain.bytes_to_screen_str((0xC0, 0xFE))[:32]
                + "1" * 32
            )
        elif self._levelscr is not None and self._levelscr > 11:
            # if levelscr > 11, then prior screen had water below, so this
            # has solid upper area.
            row = heroed.ui.terrain.bytes_to_screen_str((0xFF, 0xFF))
        else:
            # normal upper area
            row = heroed.ui.terrain.bytes_to_screen_str(
                self.uiobj.prior_screen_data[
                    hero.BYTE_LATERAL_LOW : hero.BYTE_CENTER_LOW + 1 : 2
                ]
            )
        row = row.replace("0", " ").replace("1", ACS_CKBOARD)
        row = self._terrain_color + row
        for y in range(6):
            with self.uiobj.term.location(self.pos.x, y + self.pos.y):
                print(
                    self.uiobj.term.acs(row),
                    end="",
                )

        # also draw an arrow in initial screens
        if self.uiobj.screen_number in self.uiobj.level_initial_screens:
            self.draw_initial_screen_arrow()

    def draw_terrain_mid_area(self):
        """Draw the middle area of terrain"""
        side_gap = self.uiobj.get_attribute_sidegap(self.uiobj.screen_data)

        # alternative right side gap
        row = heroed.ui.terrain.bytes_to_screen_str(
            self.uiobj.screen_data[
                hero.BYTE_LATERAL_MID : hero.BYTE_CENTER_MID + 1 : 2
            ],
            side_gap == 1,
        )
        row = row.replace("0", " ").replace("1", ACS_CKBOARD)

        # side gaps
        # initial and final screens* ignore left or right side gaps
        # *final screens > 11 don't ignore side gaps
        ignore_side_gaps = (
            self.uiobj.screen_number
            in self.uiobj.level_initial_screens
            + hero.final_screens(
                self.uiobj.level_initial_screens,
                self.uiobj.level_screen_count,
            )
            and self._levelscr is not None
            and self._levelscr < 11
        )
        if not ignore_side_gaps:
            if side_gap == 2:  # right side gap
                row = row[:-8] + " " * 8
            elif side_gap == 3:  # left side gap
                row = " " * 8 + row[8:]

        # When level screen is >= 11, then there is water, and the meaning of
        # "no side gap" changes to "both side gaps"!
        if (
            self._levelscr is not None
            and self._levelscr >= 11
            and side_gap == 0
        ):  # no side gap
            row = " " * 8 + row[8:-8] + " " * 8

        # Also when level screen is >= 11 and 'alt. right side' is on,
        # there is always left side gap, and the central-right terrain
        # is fixed clear!
        if (
            self._levelscr is not None
            and self._levelscr >= 11
            and side_gap == 1
        ):  # alternative right side
            row = " " * 8 + row[8:]
            row = row[:32] + " " * 6 + row[38:]

        # highlight cursor
        if (
            self.uiobj.mode == self.uiobj.mode_terrain
            and self.uiobj.terrain_cursor.value().y == 0  # 0 = middle area
        ):
            row = self._highlight_cursor(row)

        if self.uiobj.get_attribute_magma(self.uiobj.screen_data):
            row = self.uiobj.term.red_on_black + row
        else:
            row = self._terrain_color + row

        for y in range(6, 11):
            with self.uiobj.term.location(self.pos.x, y + self.pos.y):
                print(self.uiobj.term.acs(row), end="")

    def draw_terrain_lo_area(self):
        """Draw the lower area of terrain"""
        s = heroed.ui.terrain.bytes_to_screen_str(
            self.uiobj.screen_data[
                hero.BYTE_LATERAL_LOW : hero.BYTE_CENTER_LOW + 1 : 2
            ]
        )
        s = s.replace("0", " ").replace("1", ACS_CKBOARD)

        # highlight cursor
        if (
            self.uiobj.mode == self.uiobj.mode_terrain
            and self.uiobj.terrain_cursor.value().y == 1  # 1 = lower area
        ):
            s = self._highlight_cursor(s)

        s = self._terrain_color + s

        for y in range(11, 16):
            with self.uiobj.term.location(self.pos.x, y + self.pos.y):
                print(self.uiobj.term.acs(s), end="")

        # last row... if levelscr >= 11, then draw water. Else, draw another
        # lower area row.
        if self._levelscr is not None and self._levelscr >= 11:
            s = self.uiobj.term.cyan_on_white + ACS_CKBOARD * 64
        with self.uiobj.term.location(self.pos.x, 16 + self.pos.y):
            print(self.uiobj.term.acs(s), end="")

    def draw_initial_screen_arrow(self):
        # fmt:off
        arrow = (
            " || ",
            "_||_",
            "\\  /",
            " \\/ "
        )
        # fmt:on
        for i, line in enumerate(arrow):
            print(
                self.uiobj.term.move_xy(self.pos.x + 14, self.pos.y + 1 + i)
                + self.uiobj.term.bright_yellow_on_black(line),
                end="",
            )

    def _highlight_cursor(self, row):
        cursor_x = heroed.ui.terrain.data_to_screen_pos(
            self.uiobj.terrain_cursor.value().x
        )
        cursor_w = heroed.ui.terrain.data_to_screen_width(
            self.uiobj.terrain_cursor.value().x
        )
        return (
            row[:cursor_x]
            + self.uiobj.term.on_yellow
            + row[cursor_x : cursor_x + cursor_w]
            + self.uiobj.term.on_black
            + row[cursor_x + cursor_w :]
        )

    def draw_objects(self):
        """Draw the objects of the screen (lantern, enemies, wall)"""
        # Draw lantern
        pos_lantern = heroed.ui.objects.byte_to_position(
            self.uiobj.screen_data[hero.BYTE_LANTERN]
        )
        if pos_lantern != hero.OBJECT_HIDDEN_POS:
            self._draw_object(
                hero.BYTE_LANTERN,
                heroed.ui.objects.position_to_screen_pos(pos_lantern),
                1,
            )

        # Draw wall
        pos_wall = heroed.ui.objects.byte_to_position(
            self.uiobj.screen_data[hero.BYTE_WALL]
        )
        # initial screens have wall in fixed position 15
        if self.uiobj.screen_number in self.uiobj.level_initial_screens:
            self._draw_object(
                hero.BYTE_WALL,
                heroed.ui.objects.position_to_screen_pos(15),
                6,
            )
        elif pos_wall in range(4, 36):
            self._draw_object(
                hero.BYTE_WALL,
                heroed.ui.objects.position_to_screen_pos(pos_wall),
                6,
            )

        # Draw enemy mid
        pos_enemy_mid = heroed.ui.objects.byte_to_position(
            self.uiobj.screen_data[hero.BYTE_ENEMY_MID]
        )
        if pos_enemy_mid != hero.OBJECT_HIDDEN_POS:
            self._draw_object(
                hero.BYTE_ENEMY_MID,
                heroed.ui.objects.position_to_screen_pos(pos_enemy_mid),
                7,
            )

        # Draw enemy low
        pos_enemy_low = heroed.ui.objects.byte_to_position(
            self.uiobj.screen_data[hero.BYTE_ENEMY_LOW]
        )
        if pos_enemy_low != hero.OBJECT_HIDDEN_POS:
            self._draw_object(
                hero.BYTE_ENEMY_LOW,
                heroed.ui.objects.position_to_screen_pos(pos_enemy_low),
                12,
            )

        # Draw miner (only if it is the final screen of level)
        if self.uiobj.screen_number in hero.final_screens(
            self.uiobj.level_initial_screens, self.uiobj.level_screen_count
        ):
            self._draw_miner(pos_wall)

    def _draw_object(self, byte, x, y):
        x += self.pos.x
        y += self.pos.y
        bg_color = self.uiobj.term.on_black
        if (
            self.uiobj.mode == self.uiobj.mode_objects
            and self.uiobj.objects_cursor.value() == byte
        ):
            bg_color = self.uiobj.term.on_yellow

        with self.uiobj.term.location(x, y):
            if byte in (hero.BYTE_ENEMY_MID, hero.BYTE_ENEMY_LOW):
                enemy_type = heroed.ui.objects.byte_to_enemy_type(
                    self.uiobj.screen_data[byte]
                )
                if enemy_type == hero.ENEMY_SPIDER:
                    print(bg_color + self.uiobj.term.green(" | "))
                    print(
                        self.uiobj.term.move_x(x)
                        + bg_color
                        + self.uiobj.term.red("|V|")
                    )
                elif enemy_type == hero.ENEMY_BAT:
                    print(bg_color + self.uiobj.term.red("/V\\"))
                    print(
                        self.uiobj.term.move_x(x)
                        + bg_color
                        + self.uiobj.term.red("w^w")
                    )
                elif enemy_type == hero.ENEMY_MOTH:
                    print(
                        bg_color
                        + self.uiobj.term.white
                        + "\\"
                        + self.uiobj.term.red
                        + "~"
                        + self.uiobj.term.white
                        + "/"
                    )
                    print(
                        self.uiobj.term.move_x(x)
                        + bg_color
                        + self.uiobj.term.white
                        + "/"
                        + self.uiobj.term.red
                        + "~"
                        + self.uiobj.term.white
                        + "\\"
                    )
                elif enemy_type == hero.ENEMY_SNAKE:
                    print(bg_color + self.uiobj.term.bright_green("==C"))

            elif byte == hero.BYTE_LANTERN:
                print(
                    self.uiobj.term.move_x(x + 1)
                    + bg_color
                    + self.uiobj.term.white("/T")
                )
                print(
                    self.uiobj.term.move_x(x + 1)
                    + bg_color
                    + self.uiobj.term.white("\\/")
                )

            elif byte == hero.BYTE_WALL:
                if self.uiobj.get_attribute_magma(self.uiobj.screen_data):
                    fg_color = self.uiobj.term.red
                else:
                    fg_color = self.uiobj.term.magenta
                for _ in range(5):
                    print(
                        self.uiobj.term.move_x(x)
                        + bg_color
                        + fg_color
                        + self.uiobj.term.acs(ACS_CKBOARD * 3)
                    )

    def _draw_miner(self, pos_wall):
        with self.uiobj.term.location(self.pos.x, 9 + self.pos.y):
            if pos_wall <= 19:
                # draw at left side
                print(
                    self.uiobj.term.move_x(self.pos.x + 13)
                    + self.uiobj.term.on_black
                    + self.uiobj.term.yellow
                    + " "
                    + self.uiobj.term.acs(ACS_DIAMOND)
                )
                print(
                    self.uiobj.term.move_x(self.pos.x + 13)
                    + self.uiobj.term.on_black
                    + self.uiobj.term.green
                    + " "
                    + "O"
                    + self.uiobj.term.white
                    + "#"
                )
            else:
                # draw at right side
                print(
                    self.uiobj.term.move_x(self.pos.x + 49)
                    + self.uiobj.term.on_black
                    + self.uiobj.term.yellow
                    + " "
                    + self.uiobj.term.acs(ACS_DIAMOND)
                    + " "
                )
                print(
                    self.uiobj.term.move_x(self.pos.x + 49)
                    + self.uiobj.term.on_black
                    + self.uiobj.term.green
                    + "#"
                    + self.uiobj.term.white
                    + "O "
                )
