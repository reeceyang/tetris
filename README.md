# tetris
tetris in the terminal with python

<img width="1582" alt="Screen Shot 2023-10-24 at 11 07 23 PM" src="https://github.com/reeceyang/tetris/assets/7040416/805c1044-67d8-4bf8-bcd4-6961f0a1a11a">

to run:
```bash
python3 tetris.py
```

controls: `left`, `right`, and `down` to move the current piece. `space` to hard drop. `z` and `x` to rotate. `c` to hold.

all pieces are represented by tuples of integers: in binary a 1 indicates the piece is in that cell and a 0 indicates that it isn't. this lets us do many tetris operations through bit operations

the `Tetris` object is designed to allow for custom pieces and board sizes.

i used the `curses` library for user input and display.

possible extensions: 
 - game over checking is unimplemented. all the functionality for this theoretically exists but i couldn't get curses to print the game over message
 - adding in different colors for different pieces. i had a plan to do this by keeping $n$ versions of the board for each color, then bitwise-`or`ing all the color boards together to do the full board computations
 - rotating pieces (and input in general) feels somewhat funky compared to "real" tetris
 - adding in sound effects and music

<img width="1582" alt="Screen Shot 2023-10-24 at 1 12 18 PM" src="https://github.com/reeceyang/tetris/assets/7040416/6bd2eeab-08b8-4959-a42a-aadb8062ff3f">

_a screenshot of in-progress tetris development_
