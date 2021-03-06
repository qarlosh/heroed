__version__ = "0.3.2"

import os
import os.path
import ctypes
import shutil
import argparse
import contextlib

from heroed.editor import Editor
from heroed import hero
from heroed.ui import UI

DEFAULT_MOD_NAME = "MY FIRST MOD"


@contextlib.contextmanager
def handle_init_exceptions(parser):
    """Handle exceptions during initialization. If
    the OS is Windows, show any error in a UI dialog"""
    try:
        yield
    except Exception as err:
        if os.name == "nt":
            usage = parser.format_usage()
            MessageBox = ctypes.windll.user32.MessageBoxW
            MessageBox(
                None,
                "To use 'heroed' you must specify the 'hero.rom' file. "
                + "You can drag'n drop the rom file over 'heroed.exe' from the file explorer, "
                + "or pass it as a parameter from the command line.\n\n"
                + "Remember that 'heroed' is a console application!\n\n"
                + ("Error:\n%s\n\n" % str(err))
                + ("%s" % usage),
                "heroed error",
                0,
            )
        raise


class ArgumentParserExcept(argparse.ArgumentParser):
    def error(self, message):
        """raise exception instead of exiting
        (3.9: ArgumentParser has exit_on_error...)
        """
        raise argparse.ArgumentError(None, message)


def main_editor():
    parser = ArgumentParserExcept(
        "heroed",
        description="HEROED - MSX H.E.R.O. Editor",
    )
    parser.add_argument(
        "romfile", metavar="romfile", help="The MSX H.E.R.O. ROM file to edit"
    )
    parser.add_argument(
        "-v", "--version", action="version", version=__version__
    )

    with handle_init_exceptions(parser):
        args = parser.parse_args()
        if not os.path.isfile(args.romfile):
            raise FileNotFoundError('"%s" file not found' % args.romfile)
        editor = Editor(open(args.romfile, "r+b"))
        ui = UI()

    ui.version = __version__
    # fmt: off
    if (message_0 := editor.read_title_screen_message(0)) ==\
            hero.TITLE_SCREEN_MESSAGE_0:
        ui.mod_name = DEFAULT_MOD_NAME
    else:
        ui.mod_name = message_0[10:25].rstrip()
    # fmt: on

    def on_selected_screen_changed():
        ui.screen_number = editor.selected_screen
        ui.set_screen_data(editor.screen_data, editor.prior_screen_data)

    def on_level_layout_changed():
        ui.set_level_layout(
            editor.level_initial_screens, editor.level_screen_count
        )

    editor.signals.connect(
        "selected_screen_changed", on_selected_screen_changed
    )
    editor.signals.connect("level_layout_changed", on_level_layout_changed)

    # run main loop
    with ui.run():
        on_level_layout_changed()
        editor.selected_screen = 0
        while True:
            keystroke = ui.process_keystroke()
            if not keystroke:
                continue

            if keystroke.lower() == "q":
                editor.screen_data = ui.screen_data
                if editor.are_there_modifications():
                    if ui.confirm_message(
                        "There are unsaved changes, really quit?"
                    ):
                        break
                else:
                    break

            elif keystroke in (str(n) for n in range(10)):
                # Numbers from 0 to 9 are used to go to a specific level
                level = ui.input_quick_string(keystroke)
                if level.isnumeric() and int(level) - 1 in range(20):
                    editor.screen_data = ui.screen_data
                    editor.selected_screen = editor.level_initial_screens[
                        int(level) - 1
                    ]

            elif keystroke.code == ui.term.KEY_PGUP:
                editor.screen_data = ui.screen_data
                editor.selected_screen -= 1

            elif keystroke.code == ui.term.KEY_PGDOWN:
                editor.screen_data = ui.screen_data
                editor.selected_screen += 1

            elif keystroke.code == ui.term.KEY_HOME:
                editor.screen_data = ui.screen_data
                editor.selected_screen = 0

            elif keystroke.code == ui.term.KEY_END:
                editor.screen_data = ui.screen_data
                editor.selected_screen = 255

            elif keystroke.lower() == "s":
                # Save modifications to ROM file
                editor.screen_data = ui.screen_data
                editor.save_modified_screens_to_file()
                editor.save_level_layout_to_file()
                editor.write_title_screen_message(
                    0, "H.E.R.O.tm%s=HEROED" % ui.mod_name.ljust(15)
                )
                editor.hero_ed_rom.flush()
                ui.information_message("===========  Saved!  ===========")

            elif keystroke.lower() == "h":
                ui.show_help()

            elif keystroke.lower() == "n":
                # Modify the name of the mod
                ui.mod_name = ui.input(
                    "Enter the name of this mod:",
                    default=ui.mod_name,
                    max_length=15,
                ).upper()
                # check only permitted chars
                ui.mod_name = "".join(
                    char if char in hero.HERO_TO_ASCII else " "
                    for char in ui.mod_name
                )
                ui.draw_mod_name()

            elif keystroke.lower() == "z":
                editor.define_current_screen_as_initial()

            elif keystroke.lower() == "x":
                editor.define_current_screen_as_final()
