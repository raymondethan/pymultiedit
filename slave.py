import asyncio
import json
import curses
import sys
from editor import Editor
from random import random

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ 'key_code': data, 'x':None, 'y':None })
    protocol.user_input_received(msg)

class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, loop, editor, _id):
        self.loop = loop
        self.editor = editor
        self._id = _id

    def connection_made(self, transport):
        self.connections = set([transport])

    def data_received(self, data):
        data = json.loads(data.decode())
        if 'id' in data and self._id == data['id']: return
        if 'init_data' in data:
            self.editor.data = data['init_data']
            self.editor.init()
        else:
            self.editor.on_data_received(json.dumps(data))

    def broadcast(self, msg):
        for transport in self.connections:
            transport.write(msg)

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        data['id'] = self._id
        if self.editor.should_broadcast_edit(data['key_code']):
            self.broadcast(json.dumps(data).encode())
        self.editor.handle_key_code(data['key_code'], data['x'], data['y'])

    def connection_lost(self, exc):
        self.loop.stop()

def main(stdscr):
    stdscr.clear()

    editor = Editor(stdscr)
    loop = asyncio.get_event_loop()
    protocol = EchoClientProtocol(loop, editor, random())
    loop.add_reader(sys.stdin, got_stdin_data, protocol)
    coro = loop.create_connection(lambda: protocol,
                                          '127.0.0.1', 8888)
    transport, protocol = loop.run_until_complete(coro)
    # Serve requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass

    loop.close()

if __name__ == "__main__":
    curses.wrapper(main)

