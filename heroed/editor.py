#!/usr/bin/python3.8
""" Some useful info:

A game screen has a size of 32x17 MSX chars (256x136 px).
This is split in 3 horizontal areas, each one having an
height of 6 (upper), 5 (middle) and 6 (lower) chars, respectively.

The standard size of a terminal is 80x24 chars. This editor is
designed to fit exactly this size, and won't run on a smaller terminal.
"""

import os.path
import shutil

from heroed.utils import Signals
from heroed import hero


class Editor:
    def __init__(self, hero_ed_rom):
        self.hero_ed_rom = hero_ed_rom
        self.signals = Signals(
            "selected_screen_changed", "level_layout_changed"
        )
        self._prior_screen_data = None
        self._screen_data = None
        self._screen_original_data = None
        self._selected_screen = None
        # store each modified screen in self._screens,
        # to permit saving to disk all at once.
        self._modified_screens = {}
        self._level_layout_modified = False
        self._read_level_initial_screens()
        self._read_level_screen_count()

    def _read_screen_data(self, screen_number):
        screen_data = bytearray(8)
        for n, offset in enumerate(hero.SCREENS_TABLES_ADDRESSES):
            self.hero_ed_rom.seek(offset + screen_number)
            screen_data[n] = ord(self.hero_ed_rom.read(1))
        return screen_data

    def _read_level_initial_screens(self):
        self.hero_ed_rom.seek(hero.LEVEL_INITIAL_SCREEN_ADDRESS)
        data = self.hero_ed_rom.read(20)
        self._level_initial_screens = tuple(data)

    def _read_level_screen_count(self):
        self.hero_ed_rom.seek(hero.LEVEL_SCREEN_COUNT_ADDRESS)
        data = self.hero_ed_rom.read(20)
        self._level_screen_count = tuple(b + 1 for b in data)

    def _write_screen_data(self, screen_number, screen_data):
        for n, offset in enumerate(hero.SCREENS_TABLES_ADDRESSES):
            self.hero_ed_rom.seek(offset + screen_number)
            self.hero_ed_rom.write(screen_data[n : n + 1])

    def _write_level_initial_screens(self):
        self.hero_ed_rom.seek(hero.LEVEL_INITIAL_SCREEN_ADDRESS)
        self.hero_ed_rom.write(bytearray(self._level_initial_screens))

    def _write_level_screen_count(self):
        self.hero_ed_rom.seek(hero.LEVEL_SCREEN_COUNT_ADDRESS)
        self.hero_ed_rom.write(
            bytearray(b - 1 for b in self._level_screen_count)
        )

    def read_title_screen_message(self, message_number):
        """Read message of title screen from file.
        message_number  int, from 0 to 3
        """
        assert 0 <= message_number < 4
        offset = hero.TITLE_SCREEN_MESSAGES_ADDRESSES[message_number]
        self.hero_ed_rom.seek(offset)
        return "".join(
            hero.HERO_TO_ASCII[char] for char in self.hero_ed_rom.read(32)
        )

    def write_title_screen_message(self, message_number, message):
        """Write message of title screen to file.
        message_number  int, from 0 to 3
        message         ascii string of 32 chars
        """
        assert 0 <= message_number < 4
        assert len(message) == 32
        offset = hero.TITLE_SCREEN_MESSAGES_ADDRESSES[message_number]
        self.hero_ed_rom.seek(offset)
        self.hero_ed_rom.write(
            bytearray(hero.ASCII_TO_HERO[ord(char)] for char in message)
        )

    def _get_screen(self, screen_number):
        """get screen data, from self._modified_screens dict if it has already
        been modified, or else from file
        """
        if screen_number in self._modified_screens:
            return self._modified_screens[screen_number].copy()
        else:
            return self._read_screen_data(screen_number)

    def _get_prior_screen(self, screen_number):
        """get the prior screen data, because it is used to draw the
        higher area of the current screen.
        For initial screens, use None.
        """
        if screen_number in self.level_initial_screens:
            return None
        else:
            return self._get_screen(screen_number - 1)

    def _is_screen_data_modified(self):
        return self._screen_data != self._screen_original_data

    @property
    def level_initial_screens(self):
        return self._level_initial_screens

    @level_initial_screens.setter
    def level_initial_screens(self, value):
        """Set the level_initial_screens tuple"""
        if self._level_initial_screens == value:
            return

        self._level_initial_screens = value
        self._level_layout_modified = True
        self.signals.emit("level_layout_changed")

    @property
    def level_screen_count(self):
        return self._level_screen_count

    @level_screen_count.setter
    def level_screen_count(self, value):
        """Set the level_screen_count tuple"""
        if self._level_screen_count == value:
            return

        self._level_screen_count = value
        self._level_layout_modified = True
        self.signals.emit("level_layout_changed")

    @property
    def selected_screen(self):
        """ Get the current selected screen """
        return self._selected_screen

    @selected_screen.setter
    def selected_screen(self, value):
        """ Set the current selected screen """
        value = max(min(0xFF, value), 0x00)
        if self._selected_screen == value:
            return

        if self._selected_screen is not None:
            self.store_selected_screen()
        self._selected_screen = value
        self._screen_data = self._get_screen(self._selected_screen)
        self._prior_screen_data = self._get_prior_screen(self._selected_screen)
        self._screen_original_data = self._screen_data.copy()
        self.signals.emit("selected_screen_changed")

    def store_selected_screen(self):
        """if the current screen has been modified, store
        in self._modified_screens dict"""
        if self._is_screen_data_modified():
            self._modified_screens[
                self.selected_screen
            ] = self._screen_data.copy()
            self._screen_original_data = self._screen_data.copy()

    def restore_screen_data(self):
        # TODO: not used...
        self._screen_data = self._screen_original_data.copy()

    @property
    def screen_data(self):
        """ Get the selected screen data """
        return self._screen_data

    @screen_data.setter
    def screen_data(self, screen_data):
        """ Modify the selected screen data """
        self._screen_data = screen_data.copy()
        self.store_selected_screen()

    @property
    def prior_screen_data(self):
        """ Get the prior screen data """
        return self._prior_screen_data

    def save_modified_screens_to_file(self):
        """Write modified screens data to file and return True.
        Return False if there are not any modifications.
        """
        if not self.are_there_modified_screens():
            return False
        while len(self._modified_screens):
            self._write_screen_data(*self._modified_screens.popitem())
        return True

    def save_level_layout_to_file(self):
        """Write level_initial_screens and level_screen_count info to
        file and return True.
        Return False if there are not any modifications.
        """
        if not self._level_layout_modified:
            return False
        self._write_level_initial_screens()
        self._write_level_screen_count()
        self._level_layout_modified = False
        return True

    def are_there_modified_screens(self):
        """Returns True if there are any modified screens"""
        return len(self._modified_screens) > 0

    def is_layout_modified(self):
        return self._level_layout_modified

    def are_there_modifications(self):
        return self.are_there_modified_screens() or self.is_layout_modified()

    def define_current_screen_as_initial(self):
        """define the current screen as the initial screen of the level."""
        final_screens = hero.final_screens(
            self.level_initial_screens, self.level_screen_count
        )

        # Don't allow setting the same screen as initial and final
        if self.selected_screen in final_screens:
            return False

        search_screen = self.selected_screen
        while search_screen <= 255:
            level, _ = hero.get_levelscr_from_absscr(
                search_screen,
                self.level_initial_screens,
                self.level_screen_count,
            )
            # If the current screen is "lost", then search from
            # a posterior screen
            if level is None:
                search_screen += 1
            else:
                break

        # if the level is not found, return
        if level is None:
            return False

        # set the initial screen and current length
        # final_screen = final_screens[level - 1]

        # set level initial screen
        level_initial_screens = list(self.level_initial_screens)
        level_initial_screens[level - 1] = self.selected_screen
        self.level_initial_screens = tuple(level_initial_screens)

        # calculate the new screen count for the level
        # screen_count = final_screen - self.selected_screen + 1
        screen_count = final_screens[level - 1] - self.selected_screen + 1

        # set level length
        level_screen_count = list(self.level_screen_count)
        level_screen_count[level - 1] = screen_count
        self.level_screen_count = tuple(level_screen_count)

        return True

    def define_current_screen_as_final(self):
        """define the current screen as the final screen of the level."""

        # Don't allow setting the same screen as initial and final
        if self.selected_screen in self.level_initial_screens:
            return False

        search_screen = self.selected_screen
        while search_screen >= 0:
            level, _ = hero.get_levelscr_from_absscr(
                search_screen,
                self.level_initial_screens,
                self.level_screen_count,
            )
            # If the current screen is "lost", then search from
            # a previous screen
            if level is None:
                search_screen -= 1
            else:
                break

        # if the level is not found, return
        if level is None:
            return False

        # calculate the new screen count for the level
        screen_count = (
            self.selected_screen - self.level_initial_screens[level - 1] + 1
        )

        # set level length
        level_screen_count = list(self.level_screen_count)
        level_screen_count[level - 1] = screen_count
        self.level_screen_count = tuple(level_screen_count)

        return True
