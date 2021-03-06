import asyncio
import curses
from editor import Editor
import sys
import json
from random import random
from constants import *
from reader import Reader

# TODO:
# * multicast dns
# * if get conflict with positioning just append to end
# * how to make sure both files stay in sync?

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ KEY_CODE: data, KEY_X:None, KEY_Y:None })
    protocol.user_input_received(msg)

class MasterProtocol(asyncio.Protocol):

    def __init__(self, _id):
        self.connections = {}
        self._id = _id
        self.reader = Reader()

    def connection_made(self, transport):
        new_id = random()
        to_send = json.dumps({KEY_NEW_ID:new_id,KEY_NEW_DATA:self.editor.data}).encode()
        transport.write(to_send)
        self.connections[new_id] = transport
        self.editor.screen.clear()

    def broadcast(self, msg, ignore=None):
        for t_id in self.connections:
            if t_id == ignore: continue
            self.connections[t_id].write(msg)

    def data_received(self, data):
        data = self.reader.push(data)
        if not data: return
        for msg in data:
            msg = json.loads(msg)
            if KEY_ID not in msg: raise Exception('Msg send without ID')
            if self._id == msg[KEY_ID]: return
            t_id = msg[KEY_ID]
            self.editor.on_data_received(json.dumps(msg))
            self.broadcast(json.dumps(msg).encode(), ignore=t_id)

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
        for t_id in self.connections:
            transport = self.connections[t_id]
            if transport.is_closing():
                to_remove.add(t_id)
        for t_id in to_remove:
            del self.connections[t_id]

def main(stdscr):
    stdscr.clear()

    # check args properly passed in __main__
    fname = sys.argv[2]
    port = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_PORT
    editor = Editor(stdscr, fname)

    loop = asyncio.get_event_loop()
    protocol = MasterProtocol(random())
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

