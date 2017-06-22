import sys
import curses
import master
import slave

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Need to specify a file name and optionally a port (default is '+str(DEFAULT_PORT)+')')
        print('Run \'python main.py serve filename\' if you want to share a file with others')
        sys.exit()
    if sys.argv[1] == "run": curses.wrapper(master.main)
    else: curses.wrapper(slave.main)
