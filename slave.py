from time import sleep
import asyncio
import curses
import json
import sys

from constants import *
from editor import Editor
from random import random
from reader import Reader

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ KEY_CODE: data, KEY_X:None, KEY_Y:None })
    protocol.user_input_received(msg)

class SlaveProtocol(asyncio.Protocol):
    def __init__(self, loop, editor):
        self.loop = loop
        self.editor = editor
        self._id = None
        self.data_buff = bytearray()
        self.file_size = 0
        self.reader = Reader()

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        data = self.reader.push(data)
        if not data: return

        for msg in data: 
            msg = json.loads(msg)
            if KEY_ID in msg and self._id == msg[KEY_ID]: return
            if KEY_NEW_ID in msg:
                self._id = msg[KEY_NEW_ID]
            if KEY_NEW_DATA in msg:
                self.editor.data = msg[KEY_NEW_DATA]
                self.editor.init()
            else:
                self.editor.on_data_received(json.dumps(msg))

    def is_receiving_file(self):
        return len(self.data_buff) < self.file_size

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        data[KEY_ID] = self._id
        if self.editor.should_broadcast_edit(data[KEY_CODE]):
            self.transport.write(json.dumps(data).encode())
        self.editor.handle_key_code(data[KEY_CODE], data[KEY_X], data[KEY_Y])

    def connection_lost(self, exc):
        self.loop.stop()

def main(stdscr):
    stdscr.clear()

    ip = sys.argv[1]
    port = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_PORT

    editor = Editor(stdscr)
    loop = asyncio.get_event_loop()
    protocol = SlaveProtocol(loop, editor)

    loop.add_reader(sys.stdin, got_stdin_data, protocol)
    coro = loop.create_connection(lambda: protocol, ip, port)
    transport, protocol = loop.run_until_complete(coro)
    # Serve requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Need to specify a file name and optionally a port (default is '+str(DEFAULT_PORT)+')')
        print('Run ifconfig | grep inet to get ip address on master')
        sys.exit()
    curses.wrapper(main)
