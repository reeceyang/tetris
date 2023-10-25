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

def rotate_shape_ccw_90(shape: tuple[int]):
    """

    returns shape, new height, new width
    """
    height = len(shape)
    width = max(layer.bit_length() for layer in shape)
    # https://stackoverflow.com/questions/8421337/rotating-a-two-dimensional-array-in-python
    return tuple(int("".join(new_layer), 2) for new_layer in zip(*tuple(f"{layer:0>{width}b}" for layer in shape)[::-1]))

class Piece:
    def __init__(self, loc, shape):
        """
        loc is the position of the bottom-left corner of the piece's rectangular bounding box
        """
        self.shapes: dict[Dir, tuple[int]] = {
            Dir.N: shape,
            Dir.W: rotate_shape_ccw_90(shape),
            Dir.S: rotate_shape_ccw_90(rotate_shape_ccw_90(shape)),
            Dir.E: rotate_shape_ccw_90(rotate_shape_ccw_90(rotate_shape_ccw_90(shape))),
        }
        self.loc: Loc = loc
        self.rot: Dir = Dir.N
        self.widths = {d: max(layer.bit_length() for layer in shape) for d, shape in self.shapes.items()}
        self.heights = {d: len(shape) for d, shape in self.shapes.items()}

    def get_width(self):
        return self.widths[self.rot]

    def get_height(self):
        return self.widths[self.rot]

    def get_bits(self):
        return (layer << (self.loc.col - self.get_width()) for layer in self.shapes[self.rot])

    def rot_right(self):
        self.rot = Dir((self.rot.value + 1) % 4)

    def rot_left(self):
        self.rot = Dir((self.rot.value - 1) % 4)

    def __str__(self):
        return "\n".join(f"{layer:0>{self.get_width()}b}" for layer in reversed(self.shapes[Dir.N]))

SHAPES = {"o": (0b11, 0b11), "i": (1, 1, 1, 1), "s": (0b110, 0b011), "z": (0b011, 0b110), "j": (0b11, 1, 1), "l": (0b11, 0b10, 0b10), "t": (0b010, 0b111), 
        # "amogus": (0b01010, 0b11110, 0b11111, 0b00110)
        }

class Tetris:
    def __init__(self, height=20, width=10, starting_level=0):
        """
        row 0 is the bottommost layer
        col 0 is the rightmost column

        there is always a current piece
        """
        self.width: int = width
        self.height: int = height
        self.board: list[int] = []
        self.FULL_ROW = 2 ** width - 1
        self.current_piece: None | int = None
        self._next_piece()

        self.hold_piece: None | Piece = None
        self.cleared_lines: int = 0
        self.starting_level: int = starting_level

    def _add_piece(self, shape):
        new_piece = Piece(Loc(self.height - len(shape), self.width // 2), shape)
        assert new_piece.get_height() <= self.height
        assert new_piece.get_width() <= self.width
        self.current_piece = new_piece

    def _next_piece(self):
        self._add_piece(random.choice(list(SHAPES.values())))

    def _clear_rows(self):
        prev_num_lines = len(self.board)
        self.board = [layer for layer in self.board if layer != self.FULL_ROW]
        self.cleared_lines += prev_num_lines - len(self.board)

    def _stop_piece(self):
        shape = self.current_piece.get_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row < len(self.board):
                self.board[layer_row] |= layer
            else:
                self.board.append(layer)
        self._clear_rows()
        self._next_piece()
        self.can_hold = True

    def _is_current_piece_valid(self):
        """
        WIP
        """
        if self.current_piece.loc.row < 0:
            return False
        if self.current_piece.loc.col >= self.width:
            return False
        if self.current_piece.loc.col - self.current_piece.get_width() < 0:
            return False
        shape = self.current_piece.get_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if next_row >= len(self.board):
                break
            if self.board[next_row] & layer != 0:
                return False
        return True

    def move_down(self):
        """
        returns True if the piece was moved down, False if it was stopped
        """
        if self.current_piece.loc.row == 0:
            self._stop_piece()
            return False
        shape = self.current_piece.get_bits()
        for row, layer in enumerate(shape):
            next_row = row + self.current_piece.loc.row - 1
            if next_row >= len(self.board):
                break
            if self.board[next_row] & layer != 0:
                self._stop_piece()
                return False
        self.current_piece.loc.row -= 1
        return True

    def drop(self):
        while self.move_down():
            pass

    def move_left(self):
        if self.current_piece.loc.col == self.width:
            return
        shape = self.current_piece.get_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row >= len(self.board):
                break
            if self.board[layer_row] & (layer << 1) != 0:
                return
        self.current_piece.loc.col += 1

    def move_right(self):
        if self.current_piece.loc.col - self.current_piece.get_width() == 0:
            return
        shape = self.current_piece.get_bits()
        for row, layer in enumerate(shape):
            layer_row = row + self.current_piece.loc.row
            if layer_row >= len(self.board):
                break
            if self.board[layer_row] & (layer >> 1) != 0:
                return
        self.current_piece.loc.col -= 1

    def rot_right(self):
        # TODO: make sure move is valid
        self.current_piece.rot_right()

    def rot_left(self):
        # TODO: make sure move is valid
        self.current_piece.rot_left()

    def hold(self):
        if self.hold_piece is None:
            self.hold_piece = self.current_piece
            self._next_piece()
        elif self.can_hold:
            held_shape = self.hold_piece.shapes[Dir.N]
            self.hold_piece = self.current_piece
            self._add_piece(held_shape)
        self.can_hold = False

    def get_level(self):
        return self.starting_level + (self.cleared_lines // 10)

    def __str__(self):
        current_piece_bits = tuple(self.current_piece.get_bits())
        current_piece_row = self.current_piece.loc.row
        def get_row_num_bits(row, layer):
            if 0 <= row - current_piece_row < len(current_piece_bits):
                return layer | current_piece_bits[row - current_piece_row]
            return layer
        return "\n".join(f"{get_row_num_bits(self.height - i - 1, layer):0>{self.width}b}" for i, layer in enumerate(chain([0] * (self.height - len(self.board)), reversed(self.board))))
     
def main(stdscr):
    stdscr.nodelay(True)
    stdscr.leaveok(True)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_BLACK)

    t = Tetris(starting_level=8)
    NS_PER_FRAME = 800 * 1000 * 1000
    NS_PER_LEVEL = 50 * 1000 * 1000
    countdown_start = time.time_ns()

    def print_board():
        stdscr.clear()
        for c in str(t):
            stdscr.addch(c, curses.color_pair(1 if c == "1" else 2))
        stdscr.addstr(f"""

HOLD:
""")
        for c in str(t.hold_piece):
            stdscr.addch(c, curses.color_pair(1 if c == "1" else 2))
        stdscr.addstr(f"""

CLEARED LINES: {t.cleared_lines}

LEVEL: {t.get_level()}
""")

    print_board()
    while True:
        ch = stdscr.getch()
        if ch == curses.KEY_DOWN:
            t.move_down()
        if ch == curses.KEY_LEFT:
            t.move_left()
        if ch == curses.KEY_RIGHT:
            t.move_right()
        if ch == ord(" "):
            t.drop()
        if ch == ord("x"):
            t.rot_right()
        if ch == ord("z"):
            t.rot_left()
        if ch == ord("c"):
            t.hold()
        if ch != curses.ERR:
            print_board()
        if time.time_ns() - countdown_start >= NS_PER_FRAME - t.get_level() * NS_PER_LEVEL:
            countdown_start = time.time_ns()
            t.move_down()
            print_board()

if __name__ == "__main__":
    curses.wrapper(main)
