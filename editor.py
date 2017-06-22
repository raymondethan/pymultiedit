import sys
import curses
import pickle
from os import remove
import asyncio
from json import loads

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
        self.data = self.get_contents(fname).split(self.NEW_LINE) if fname else []
        self.fname = fname or 'tmp'
        self.x = 0
        self._y = 0
        self.height, self.width = self.get_screen_yx()
        self.offset_from_top = 0
        self.err_msg = ""

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
        # gets rid of bug where old last line not cleared from screen
        output[-1] = output[-1] + ''.join([' ' for i in range(len(output[-1]),self.width)])
        if len(output) < self.height:
            output += ["~" for i in range(0, self.height-len(output))]
        return self.string_of_data(output)

    def display(self):
        self.screen.addstr(0, 0, self.fit_data_to_screen())
        self.screen.addstr(self.height, 0, self.err_msg)
        self.err_msg = " "*self.width

    def parse_input_data(self, msg):
        msg = loads(msg)
        key_code = int(msg['key_code'])
        x = msg['x'] if msg['x'] != None else self.x
        y = msg['y'] if msg['y'] != None else  self.y()
        return {
            'key_code': key_code,
            'x': x,
            'y': y
        }

    def on_data_received(self, msg):
        data = self.parse_input_data(msg)
        self.write(data['key_code'], data['x'], data['y'])
        self.display()
        self.screen.refresh()

    def handle_key_code(self, key_code, x, y):
        if self.is_cmd_start(key_code):
            self.handle_cmd()
        else:
            self.set_cursor(key_code)
        if self.is_exit(key_code):
            self.remove_file(self.backup_fname())
            sys.exit()
        elif self.should_broadcast_edit(key_code):
            self.write(key_code, x, y)
        self.display()
        self.screen.move(self.raw_y(),self.x) 
        self.screen.refresh()

    def should_broadcast_edit(self, key_code):
        return (
            not self.is_move(key_code) and
            not self.is_cmd_start(key_code) and
            not self.is_exit(key_code)
        )

    def init(self):
        self.dump_file(self.backup_fname())
        self.display()
        self.screen.move(self.raw_y(),self.x)
        self.screen.refresh()

    def run_editor(self):
        self.init()
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
            self.screen.refresh()

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
        if key_code == curses.KEY_UP:
            if self.raw_y() > 0:
                self.set_raw_y(self.raw_y()-1)
            else:
                if self.offset_from_top > 0:
                    self.offset_from_top -= 1
        elif key_code == curses.KEY_DOWN:
            if self.raw_y() < min(self.height-1,len(self.data)-1):
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
    
    fname = sys.argv[1] if len(sys.argv) > 1 else 'tmp.txt' 
    editor = Editor(stdscr, fname)
    editor.run_editor()

if __name__ == "__main__":
    curses.wrapper(main)
