# encoding=latin-1

"""
Alternate Character Set, box-drawing VT100 style.
some links with info:
    https://en.wikipedia.org/wiki/DEC_Special_Graphics
    https://en.wikipedia.org/wiki/Box-drawing_character#Unix.2C_CP.2FM.2C_BBS
    https://linux.die.net/man/5/terminfo (search 'Line Graphics')
    http://www.melvilletheatre.com/articles/ncurses-extended-characters/index.html

Alt. Char codes:
    0x60 ` ◆  ACS_DIAMOND
    0x61 a ▒  ACS_CKBOARD
    0x62 b ␉
    0x63 c ␌
    0x64 d ␍
    0x65 e ␊
    0x66 f °  ACS_DEGREE
    0x67 g ±
    0x68 h ␤
    0x69 i ␋
    0x6a j ┘  ACS_LRCORNER
    0x6b k ┐  ACS_URCORNER
    0x6c l ┌  ACS_ULCORNER
    0x6d m └  ACS_LLCORNER
    0x6e n ┼  ACS_PLUS
    0x6f o ⎺  ACS_S1
    0x70 p ⎻  ACS_S3
    0x71 q ─  ACS_HLINE (ACS_S5)
    0x72 r ⎼  ACS_S7
    0x73 s ⎽  ACS_S9
    0x74 t ├  ACS_LTEE
    0x75 u ┤  ACS_RTEE
    0x76 v ┴  ACS_BTEE
    0x77 w ┬  ACS_TTEE
    0x78 x │  ACS_VLINE
    0x79 y ≤
    0x7a z ≥
    0x7b { π
    0x7c | �
    0x7d } £
    0x7e ~ ·  ACS_BULLET
"""
ACS_LRCORNER = "j"  # ┘
ACS_URCORNER = "k"  # ┐
ACS_ULCORNER = "l"  # ┌
ACS_LLCORNER = "m"  # └
ACS_PLUS = "n"  # ┼
ACS_HLINE = "q"  # ─
ACS_LTEE = "t"  # ├
ACS_RTEE = "u"  # ┤
ACS_BTEE = "v"  # ┴
ACS_TTEE = "w"  # ┬
ACS_VLINE = "x"  # │
ACS_DIAMOND = "`"  # ◆
ACS_CKBOARD = "a"  # ▒
ACS_BULLET = "~"  # ·


def draw_msx_palette(term, x, y):
    """MSX palette representation mixing terminal colors using
    a dithered char (foreground+background colors).
    """
    msx_colors_pairs = (
        (term.black, term.on_black),  # 0 - transp
        (term.black, term.on_black),  # 1 - black
        (term.green, term.on_green),  # 2 - (medium) green
        (term.green, term.on_white),  # 3 - light green
        (term.blue, term.on_blue),  # 4 - (dark) blue
        (term.blue, term.on_white),  # 5 - light blue
        (term.red, term.on_black),  # 6 - dark red
        (term.cyan, term.on_white),  # 7 - cyan
        (term.red, term.on_red),  # 8 - (medium) red
        (term.red, term.on_white),  # 9 - light red
        (term.yellow, term.on_yellow),  # 10 - (dark) yellow
        (term.yellow, term.on_white),  # 11 - light yellow
        (term.green, term.on_black),  # 12 - dark green
        (term.magenta, term.on_magenta),  # 13 - purple
        (term.white, term.on_black),  # 14 - grey
        (term.white, term.on_white),  # 15 - white
    )

    with term.location():
        print(
            term.acs(
                term.move_xy(x, y)
                + "".join(
                    pair[0] + pair[1] + ACS_CKBOARD * 2
                    for pair in msx_colors_pairs[:8]
                )
                + term.move_xy(x, y + 1)
                + "".join(
                    pair[0] + pair[1] + ACS_CKBOARD * 2
                    for pair in msx_colors_pairs[8:]
                )
            )
        )
