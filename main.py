import sys
import curses
import pickle
from os import remove

# TODO: delete newline when backspace at x = 0
# TODO: scrolling
class Editor:

    KEY_DELETE = 127
    KEY_NEWLINE = 10
    KEY_ESC = 27
    KEY_COLON = 58
    NEW_LINE = "\n"

    def __init__(self, stdscr, fname=None):
        self.screen = stdscr
        self.fname = fname
        self.data = self.get_contents(fname).split(self.NEW_LINE) if fname else []
        self.x = 0
        self._y = 0
        self.height, self.width = self.get_screen_yx()
        self.offset_from_top = 0
        self.err_msg = None

    def y(self):
        return self._y + self.offset_from_top

    def raw_y(self):
        return self._y

    def set_raw_y(self, y):
        self._y = y

    def string_of_data(self, data):
        return self.NEW_LINE.join(data)

    def get_screen_yx(self):
        y,x = self.screen.getmaxyx()
        return (y-1,x-1)

    def fit_data_to_screen(self):
        start = self.offset_from_top
        output = [
                row[:self.width] for row in self.data[start:start+self.height]
        ]
        if len(output) < self.height:
            output += ["~" for i in range(0, self.height-len(output))]
        return self.string_of_data(output)

    def display(self):
        self.screen.addstr(0, 0, self.fit_data_to_screen())
        if self.err_msg:
            self.screen.addstr(self.height, 0, self.err_msg, curses.COLOR_RED)
            self.err_msg = None
        self.screen.refresh()

    def run_editor(self):
        self.dump_file(self.backup_fname())
        self.display()
        self.screen.move(self.raw_y(),self.x)
        while True:
            key_code = self.screen.getch()
            if self.is_exit(key_code):
                self.remove_file(self.backup_fname())
                sys.exit()
            if self.is_cmd_start(key_code):
                self.handle_cmd()
                continue
            if not self.is_move(key_code):
                self.write(key_code, self.x, self.y())
            self.set_cursor(key_code)
            self.display()
            self.screen.move(self.raw_y(),self.x) 

    def is_move(self, key):
        return key in [curses.KEY_UP, curses.KEY_DOWN, curses.KEY_LEFT, curses.KEY_RIGHT]

    def is_exit(self, key):
        return key == self.KEY_ESC

    def is_cmd_start(self, key):
        return key == self.KEY_COLON

    def write(self, key, x, y):
        new_line = list(self.data[y])
        if key == self.KEY_DELETE:
            if x > 0:
                del new_line[x-1]
        else:
            key = self.map_code_to_char(key) or curses.keyname(key).decode('utf-8')
            new_line.insert(x, key)
        self.data[y] = "".join(new_line)
        self.data = (self.string_of_data(self.data)).split(self.NEW_LINE)

    def set_cursor(self, key_code):
        y_bound = min(len(self.data)-1, self.height)
        if key_code == curses.KEY_UP:
            if self.raw_y() > 0:
                self.set_raw_y(self.raw_y()-1)
            else:
                if self.offset_from_top > 0:
                    self.offset_from_top -= 1
        elif key_code == curses.KEY_DOWN:
            if self.raw_y() < self.height:
                self.set_raw_y(self.raw_y()+1)
            else:
                if self.offset_from_top < (len(self.data)-self.height-1):
                    self.offset_from_top += 1 
        elif key_code == curses.KEY_LEFT:
            self.x = self.x - 1 if self.x > 0 else self.x
        elif key_code == curses.KEY_RIGHT:
            self.x = self.x + 1 if self.x < self.width else self.x
        elif key_code == self.KEY_NEWLINE:
            if self.raw_y() < self.height:
                self.set_raw_y(self.raw_y()+1)
            else:
                self.offset_from_top += 1
            self.x = 0
        elif key_code == self.KEY_DELETE:
            self.x = self.x - 1 if self.x > 0 else self.x
        else:
            self.x = self.x + 1 if self.x < self.width else self.x
        x_bound = min(len(self.data[self.y()]), self.width)
        if self.x > x_bound:
            self.x = x_bound

    def handle_cmd(self):
        key = self.screen.getch()
        cmd = ""
        while key != self.KEY_NEWLINE:
            cmd += str(key)
            key = self.screen.getch()
        self.execute_cmd(cmd)

    def execute_cmd(self, cmd):
        if cmd == "119":
            self.write_file(self.fname)
        else:
            self.err_msg = "Error: unrecognized command"

    def map_code_to_char(self, key_code):
        if key_code == self.KEY_NEWLINE:
            return "\n"
        return None

    def dump_file(self, fname):
        with open(fname,"wb") as f:
            pickle.dump(self.data, f)

    def write_file(self, fname):
        with open(fname,"w") as f:
            f.write(self.string_of_data(self.data))

    def remove_file(self, fname):
        remove(fname)

    def backup_fname(self):
        return "."+self.fname+".swp"

    def get_contents(self, fname):
        with open(fname) as f:
            return f.read()

def main(stdscr):
    stdscr.clear()
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    editor = Editor(stdscr, fname)
    editor.run_editor()

if __name__ == "__main__":
    curses.wrapper(main)
