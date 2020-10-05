import os.path
import shutil
import argparse

from heroed.editor import Editor
from heroed import hero
from heroed.ui import UI


VERSION = "0.2"
DEFAULT_MOD_NAME = "MY FIRST MOD"


def main():
    parser = argparse.ArgumentParser(
        "heroed", description="HEROED - MSX H.E.R.O. Editor"
    )
    parser.add_argument(
        "romfile", metavar="romfile", help="The MSX H.E.R.O. ROM file to edit"
    )
    args = parser.parse_args()

    if not os.path.isfile(args.romfile):
        raise FileNotFoundError('"%s" file not found' % args.romfile)

    editor = Editor(open(args.romfile, "r+b"))

    ui = UI()
    ui.version = VERSION
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

    editor.signals.connect(
        "selected_screen_changed", on_selected_screen_changed
    )

    # run main loop
    with ui.run():
        editor.selected_screen = 0
        while True:
            keystroke = ui.process_keystroke()
            if not keystroke:
                continue

            if keystroke.lower() == "q":
                editor.screen_data = ui.screen_data
                if editor.are_there_modified_screens():
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
                    editor.selected_screen = hero.initial_screens()[
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
                editor.write_title_screen_message(
                    0, "H.E.R.O.tm%s=HEROED" % ui.mod_name.ljust(15)
                )
                editor.hero_ed_rom.flush()
                ui.information_message("===========  Saved!  ===========")

            elif keystroke.lower() == "h":
                ui.show_help()

            elif keystroke.lower() == "d":
                ui.show_screen_data = not ui.show_screen_data
                ui.draw_screen_data()

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


if __name__ == "__main__":
    main()
