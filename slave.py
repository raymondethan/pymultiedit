import asyncio
import json
import curses
import sys
from editor import Editor
from random import random
from constants import *

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ KEY_CODE: data, KEY_X:None, KEY_Y:None })
    protocol.user_input_received(msg)

class SlaveProtocol(asyncio.Protocol):
    def __init__(self, loop, editor, _id):
        self.loop = loop
        self.editor = editor
        self._id = _id
        self.data_buffer = bytearray()

    def connection_made(self, transport):
        self.transport = transport

    def eof_received(self):
        data = json.loads(self.data_buffer)
        if KEY_ID in data and self._id == data[KEY_ID]: return
        if KEY_INIT in data:
            self.editor.data = data[KEY_INIT]
            self.editor.init()
        else:
            self.editor.on_data_received(json.dumps(data))

    def data_received(self, data):
        self.data_buffer += data
        #_data = data
        #try:
        #    data = json.loads(data.decode())
        #    if KEY_ID in data and self._id == data[KEY_ID]: return
        #    if KEY_INIT in data:
        #        self.editor.data = data[KEY_INIT]
        #        self.editor.init()
        #    else:
        #        self.editor.on_data_received(json.dumps(data))
        #except Exception as e:
        #    with open('logfile','w') as f:
        #        f.write(str(e))
        #        f.write("\n")
        #        f.write(_data.decode())

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
    protocol = SlaveProtocol(loop, editor, random())

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
