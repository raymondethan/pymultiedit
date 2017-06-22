import asyncio
import curses
from editor import Editor
import sys
import json
from random import random
from constants import *
from urllib import request

# TODO: 
# * multicast dns
# * delete newlines

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ KEY_CODE: data, KEY_X:None, KEY_Y:None })
    protocol.user_input_received(msg)

class EchoServerClientProtocol(asyncio.Protocol):

    def __init__(self, _id):
        self.connections = set()
        self._id = _id
    
    def connection_made(self, transport):
        transport.write(json.dumps({
            KEY_INIT:self.editor.data,
        }).encode())
        self.connections.add(transport)

    def broadcast(self, msg):
        for transport in self.connections:
            transport.write(msg)

    def data_received(self, data):
        msg = json.loads(data.decode())
        if KEY_ID in msg and self._id == msg[KEY_ID]: return
        self.editor.on_data_received(json.dumps(msg))
        self.broadcast(json.dumps(msg).encode())

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        data[KEY_ID] = self._id
        if self.editor.should_broadcast_edit(data[KEY_CODE]):
            self.broadcast(json.dumps(data).encode())
        self.editor.handle_key_code(data[KEY_CODE], data[KEY_X], data[KEY_Y])

    def set_editor(self, editor):
        self.editor = editor

    def init_editor(self):
        self.editor.init()

    def connection_lost(self, exn):
        to_remove = set()
        for transport in self.connections:
            if transport.is_closing():
                to_remove.add(transport)
        self.connections -= to_remove

def main(stdscr):
    stdscr.clear()
    
    # check args properly passed in __main__
    fname = sys.argv[2]
    port = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PORT
    editor = Editor(stdscr, fname)
    
    loop = asyncio.get_event_loop()
    protocol = EchoServerClientProtocol(random())
    protocol.set_editor(editor)
    protocol.init_editor()
    loop.add_reader(sys.stdin, got_stdin_data, protocol)

    # Each client connection will create a new protocol instance
    coro = loop.create_server(lambda: protocol, '0.0.0.0', port)
    server = loop.run_until_complete(coro)
    
    # Serve requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    
    # Close the server
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Need to specify a file name and optionally a port (default is '+str(DEFAULT_PORT)+')') 
        sys.exit()
    curses.wrapper(main)

