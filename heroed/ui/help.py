# encoding=latin-1
def draw_help_1(term, **kwargs):
    with term.location(0, 0):
        print(
            term.bright_yellow_on_red(
                (
                    "HEROED - MSX H.E.R.O. Editor v%s (by @qarlosherrero)"
                    % kwargs.get("ver")
                ).center(80)
            ),
            end="",
        )
        print(
            """\


Use this utility to edit the screens of the video game H.E.R.O. for MSX.

The game has 20 levels, each one with a different number of screens, for a
total amount of 256 screens.

There are two edit modes, one for Terrain and other for Objects. You can edit
the terrain of each screen and modify the objects. These objects are:

 - The lantern at the top of the screen
 - The wall at the middle
 - The two enemies at the middle and bottom.

The objects can be moved horizontally or hidden.

The default screen flow is to enter from above and to exit from below. You can
open a gap to the left or right side of a screen to enable a horizontal flow.
        """
        )


def draw_help_2(term, **kwargs):
    with term.location(0, 0):
        print(
            """\
CONTROLS

  PAGE UP           Previous screen
  PAGE DOWN         Next screen
  HOME              First screen (0)
  END               Las screen (355)
  NUMBERS           Enter a sequence of 1 or 2 numbers, and optionally end with
                    ENTER, to go to the first screen of the entered level (1 to
                    20)
  TAB               Switch between TERRAIN or OBJECT editing modes
  DIRECTION KEYS    move the terrain cursor, the selected object or select an
                    attribute
  SPACE BAR         Edit terrain, change the selected enemy type, or change an
                    attribute value
  S                 Save (overwrite current ROM file)
  N                 Change the MOD name
  H                 Show this help
  D                 Show/hide the 8 bytes of the current screen definition
  Q                 Quit
        """
        )


def draw_help_3(term, **kwargs):
    with term.location(0, 0):
        print(
            """\
TIPS

- Move an object all the way to the left or right to hide it. Use SPACE to
  cycle the 4 types of enemies.

- When the SIDE GAP attribute is 'Left' or 'Right', the Wall is hidden.

- The direction (DIR.) attribute is used when there is some side gap, to
  indicate the correct flow. Set it correctly!:
  left to right (-->) means that a left gap leads to the previous screen, and
  a right gap leads to the next screen.
  right to left (<--) means that a left gap leads to the next screen, and a
  right gap leads to the previous screen.

- From the 11th screen of each level, there is water at the bottom, so the exit
  must be to the left or right. The SIDE GAP attribute 'No' value changes to
  'Both'.

- The terrain is divided in three areas (higher, middle and lower). The higher
  area depends on the previous screen and cannot be modified directly. The
  middle and lower areas can be edited. The left and right halves are
  simmetrical.
        """
        )


def draw_help_4(term, **kwargs):
    with term.location(0, 0):
        print(
            """\
- The ALT. LAYOUT attribute toggles an alternative screen layout. When ON, the
  right half of the terrain middle area is reversed horizontally, and a side
  gap in the right side can be opened. Also, in the center-right there is a
  fixed terrain that cannot be removed. Moreover, in screens with water at
  the bottom, this behaves somewhat differently... better experiment with it.

- The initial screen of each level has some limitations, cannot have a side
  gap and the wall is always in a fixed position.

- The final screen of each level cannot have side gaps either. Also, the miner
  is positioned depending on the wall position or the SIDE GAP attribute value.

- There are some preset terrain configurations that enable some features:

    Open/close magma barrier: Enable the MAGMA attribute and fill the middle
    terrain area, leaving a narrow pit in the center.

    Water platform: In water screens, clear the lower terrain area leaving only
    a shore of a size of 2 blocks at each side.

    Octopus: It works the same as the water platform, but using a size of 3
    blocks.
        """
        )


draw_help_funcs = (draw_help_1, draw_help_2, draw_help_3, draw_help_4)
