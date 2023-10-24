from enum import Enum
from dataclasses import dataclass
from itertools import chain
import random
import curses
import time

@dataclass
class Loc:
    row: int
    col: int

class Dir(Enum):
    N = 0
    E = 1
    S = 2
    W = 3

def rotRight(d: Dir):
    return Dir((d.value + 1) % 4)

def rotLeft(d: Dir):
    return Dir((d.value - 1) % 4)

class Piece:
    def __init__(self, loc, shape):
        """
        loc is the position of the bottom-left corner of the piece's rectangular bounding box
        """
        self.shape: tuple[int] = shape
        self.loc: Loc = loc
        self.rot: Dir = Dir.N
        self.height = len(shape)
        self.width = max(layer.bit_length() for layer in shape)

    def get_current_bits(self):
        return (layer << (self.loc.col - self.width) for layer in self.shape)
    
    def __str__(self):
        return f"Piece[row: {self.row}, col: {self.col}, shape: {self.shape}]"

SHAPES = {"o": (0b11, 0b11), "i": (1, 1, 1, 1), "s": (0b110, 0b011), "z": (0b011, 0b110), "j": (0b11, 1, 1), "l": (0b11, 0b10, 0b10), "t": (0b010, 0b111)}

class Tetris:
    def __init__(self, height=20, width=10):
        """
        row 0 is the bottommost layer
        col 0 is the rightmost column

        there is always a current piece
        """
        self.width: int = width
        self.height: int = height
        self.board: list[int] = [127,127,255,255]
        self.FULL_ROW = 2 ** width - 1
        self.current_piece: None | int = None
        self._next_piece()

    def _add_piece(self, shape):
        new_piece = Piece(Loc(self.height, self.width), shape)
        assert new_piece.height <= self.height
        assert new_piece.width <= self.width
        self.current_piece = new_piece

    def _next_piece(self):
        self._add_piece(random.choice(list(SHAPES.values())))

    def _clear_rows(self):
        self.board = [layer for layer in self.board if layer != self.FULL_ROW]

    def _stop_piece(self):
        shape = self.current_piece.get_current_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row < len(self.board):
                self.board[layer_row] |= layer
            else:
                self.board.append(layer)
        self._clear_rows()
        self._next_piece()

    def move_down(self):
        if self.current_piece.loc.row == 0:
            self._stop_piece()
            return
        shape = self.current_piece.get_current_bits()
        for row, layer in enumerate(shape):
            next_row = row + self.current_piece.loc.row - 1
            if next_row >= len(self.board):
                break
            if self.board[next_row] & layer != 0:
                self._stop_piece()
                return
        self.current_piece.loc.row -= 1

    def move_left(self):
        if self.current_piece.loc.col == self.width:
            return
        shape = self.current_piece.get_current_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row >= len(self.board):
                break
            if self.board[layer_row] & (layer << 1) != 0:
                return
        self.current_piece.loc.col += 1

    def move_right(self):
        if self.current_piece.loc.col - self.current_piece.width == 0:
            return
        shape = self.current_piece.get_current_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row >= len(self.board):
                break
            if self.board[layer_row] & (layer >> 1) != 0:
                return
        self.current_piece.loc.col -= 1

    def __str__(self):
        current_piece_bits = tuple(self.current_piece.get_current_bits())
        current_piece_row = self.current_piece.loc.row
        def get_row_num_bits(row, layer):
            if 0 <= row - current_piece_row < len(current_piece_bits):
                return layer | current_piece_bits[row - current_piece_row]
            return layer
        return "\n".join(f"{get_row_num_bits(self.height - i - 1, layer):0>{self.width}b}" for i, layer in enumerate(chain([0] * (self.height - len(self.board)), reversed(self.board))))
     
def main(stdscr):
    stdscr.nodelay(True)

    t = Tetris()
    NS_PER_FRAME = 800 * 1000 * 1000
    countdown_start = time.time_ns()

    def print_board():
        stdscr.clear()
        for c in str(t):
            curses.init_pair(1, curses.COLOR_RED, curses.COLOR_WHITE)
            curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_WHITE)
            stdscr.addch(c, curses.color_pair(1 if c == "1" else 0))

    print_board()
    while True:
        ch = stdscr.getch()
        if ch == ord("s"):
            t.move_down()
        if ch == ord("a"):
            t.move_left()
        if ch == ord("d"):
            t.move_right()
        if ch != curses.ERR:
            print_board()
        if time.time_ns() - countdown_start >= NS_PER_FRAME:
            countdown_start = time.time_ns()
            t.move_down()
            print_board()

if __name__ == "__main__":
    curses.wrapper(main)
