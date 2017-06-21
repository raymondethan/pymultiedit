import asyncio
import json
import curses
import sys
from editor import Editor

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ 'key_code': data, 'x':None, 'y':None })
    protocol.user_input_received(msg)

class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, loop, editor):
        self.loop = loop
        self.editor = editor

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        data = data.decode()
        if 'init_data' in data:
            data = json.loads(data)
            self.editor.data = data['init_data']
            self.editor.init()
        else:
            self.editor.on_data_received(data)

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        if self.transport and self.editor.should_broadcast_edit(data['key_code']):
            self.transport.write(json.dumps(data).encode())
        self.editor.handle_key_code(data['key_code'], data['x'], data['y'])

    def connection_lost(self, exc):
        self.loop.stop()

def main(stdscr):
    stdscr.clear()

    editor = Editor(stdscr)
    loop = asyncio.get_event_loop()
    protocol = EchoClientProtocol(loop, editor)
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

