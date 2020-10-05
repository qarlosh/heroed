from dataclasses import dataclass


def clamp(value, min_, max_):
    """clamp a value between (inclusive) min and max values"""
    return max(min(max_, value), min_)


@dataclass
class Point:
    """Simple point type"""

    x: int
    y: int


class Signals:
    """Godot style signals, using emit() and connect()"""

    def __init__(self, *signals):
        """signals is a  list of signal names (str)"""
        self._signals = signals
        self._connections = {signal: [] for signal in self._signals}

    def connect(self, signal, fn):
        """add a function to the list of connections of a signal"""
        self._connections[signal].append(fn)

    def disconnect(self, signal, fn):
        """remove a function from the list of connections of a signal"""
        # TODO: not tested...
        self._connections[signal].remove(fn)

    def emit(self, signal):
        """run all the functions connected to a signal"""
        for conn in self._connections[signal]:
            conn()
