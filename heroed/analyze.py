from blessed import Terminal
import hero
from heroed import HEROEditor

SCREEN_DATA_BYTES_NAMES = (
    "ENEMY LOWER",
    "ENEMY MIDDLE",
    "LANTERN",
    "MIDDLE LATERAL TERRAIN",
    "LOWER LATERAL TERRAIN",
    "MIDDLE CENTER TERRAIN",
    "LOWER CENTER TERRAIN",
    "WALL & MISC",
)


def analyze_screen_data(f):
    """Print some information about the screens. Useful to analyze
    the original ROM data.

    f   file object with "rb" mode
    """
    editor = HEROEditor(f)
    term = Terminal()

    def analyze_screens(screens_iter):
        screen_data_bytes = [list() for i in range(8)]

        # get all 256 screens data bytes
        for i in screens_iter:
            # level, levelscr = get_levelscr_from_absscr(screen_number)
            editor.selected_screen = i
            for j in range(8):
                screen_data_bytes[j].append(editor.screen_data[j])

        # reduce unique bytes
        for i in range(8):
            screen_data_bytes[i] = set(screen_data_bytes[i])

        return screen_data_bytes

    def print_screens(screens, msg):
        print(term.bold_cyan(msg))
        for i in range(8):
            print(
                term.bright_yellow("%s BYTE (%d unique values)")
                % (SCREEN_DATA_BYTES_NAMES[i], len(screens[i]))
            )
            print(" ".join("%02X" % b for b in sorted(screens[i])))
        print()

    first_screens = hero.first_screen_per_level()
    print_screens(
        analyze_screens(first_screens), "UNIQUE BYTES IN INITIAL SCREENS:"
    )

    final_screens = list(
        s - 1 for s in (hero.first_screen_per_level()[1:] + [256])
    )
    print_screens(
        analyze_screens(final_screens), "UNIQUE BYTES IN FINAL SCREENS:"
    )

    firstandfinal_screens = set(first_screens + final_screens)
    all_screens = set(range(256))
    between_screens = all_screens.difference(firstandfinal_screens)

    downwards_screens = between_screens.difference(
        set(hero.horizontal_screens())
    )
    print_screens(
        analyze_screens(downwards_screens),
        "UNIQUE BYTES IN BETWEEN SCREENS (DOWNWARDS):",
    )

    leftwards_screens = set(hero.leftwards_screens())
    print_screens(
        analyze_screens(leftwards_screens),
        "UNIQUE BYTES IN BETWEEN SCREENS (LEFTWARDS):",
    )

    rightwards_screens = set(hero.rightwards_screens())
    print_screens(
        analyze_screens(rightwards_screens),
        "UNIQUE BYTES IN BETWEEN SCREENS (RIGHTWARDS):",
    )
