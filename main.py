import sys
import curses

# TODO: delete newline when backspace at x = 0
class Editor:

    KEY_DELETE = 127
    KEY_NEWLINE = 10
    NEW_LINE = "\n"

    def __init__(self, stdscr, data):
        self.screen = stdscr
        self.data = data.split(self.NEW_LINE)
        self.x = 0
        self.y = 0
        self.height, self.width = self.get_screen_yx()

    def get_screen_yx(self):
        y,x = self.screen.getmaxyx()
        return (y-1,x-1)

    def fit_to_screen(self):
        output = [row[:self.width] for row in self.data]
        if len(output) < self.height:
            output += ["~" for i in range(0, self.height-len(output))]
        return self.NEW_LINE.join(output[:self.height])

    def display(self):
        self.screen.addstr(0, 0, self.fit_to_screen())
        # refresh redraws screen
        self.screen.refresh()

    def run_editor(self):
        self.display()
        self.screen.move(self.y,self.x)
        while True:
            key_code = self.screen.getch()
            if not self.is_move(key_code):
                self.write(key_code, self.x, self.y)
            self.set_cursor(key_code)
            self.display()
            self.screen.move(self.y,self.x) 
    def is_move(self, key):
        return key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]

    def write(self, key, x, y):
        new_line = list(self.data[y])
        if key == self.KEY_DELETE:
            if x > 0:
                del new_line[x-1]
        else:
            key = self.map_code_to_char(key) or curses.keyname(key).decode('utf-8')
            new_line.insert(x, key)
        self.data[y] = "".join(new_line)
        self.data = (self.NEW_LINE.join(self.data)).split(self.NEW_LINE)

    def set_cursor(self, key_code):
        y_bound = min(len(self.data)-1, self.height)
        if key_code == curses.KEY_UP:
            self.y = self.y - 1 if self.y > 0 else self.y
        elif key_code == curses.KEY_DOWN:
            self.y = self.y + 1 if self.y < y_bound else self.y
        elif key_code == curses.KEY_LEFT:
            self.x = self.x - 1 if self.x > 0 else self.x
        elif key_code == curses.KEY_RIGHT:
            self.x = self.x + 1 if self.x < self.width else self.x
        elif key_code == self.KEY_NEWLINE:
            self.y = self.y + 1 if self.y < self.height else self.y
            self.x = 0
        elif key_code == self.KEY_DELETE:
            self.x = self.x - 1 if self.x > 0 else self.x
        else:
            self.x = self.x + 1 if self.x < self.width else self.x
        x_bound = min(len(self.data[self.y]), self.width)
        if self.x > x_bound:
            self.x = x_bound

    def map_code_to_char(self, key_code):
        if key_code == self.KEY_NEWLINE:
            return "\n"
        return None

def get_contents(fname):
    with open(fname) as f:
        return f.read()

def main(stdscr):
    stdscr.clear()
    contents = get_contents(sys.argv[1]) if len(sys.argv) > 1 else ""
    editor = Editor(stdscr, contents)
    editor.run_editor()

if __name__ == "__main__":
    curses.wrapper(main)
