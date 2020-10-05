class Cursor:
    def __init__(self):
        self._previous_cursor = None
        self._cursor = None

    def handle(self, keystroke, screen_data):
        """
        Handle the cursor
        keystroke           blessed Terminal keystroke
        screen_data         the 8 bytes of data of the screen.

        returns tuple with new cursor and screen_data
        """
        self._previous_cursor = self._cursor
        return screen_data

    def is_in_attributes(self):
        """if the cursor is in the attributes bar, below the game screen"""
        return False

    def exit_attributes(self):
        pass

    def enter_attributes(self):
        pass

    def to_str(self):
        """return str of length 14"""
        return "              "

    def value(self):
        return self._cursor

    def previous_value(self):
        return self._previous_cursor
