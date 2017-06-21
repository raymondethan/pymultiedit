import asyncio
import curses
from editor import Editor
import sys
import json

# TODO: 
# * multicast dns
# * multiple users
# * delete newlines

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ 'key_code': data, 'x':None, 'y':None })
    protocol.user_input_received(msg)

class EchoServerClientProtocol(asyncio.Protocol):

    def __init__(self):
        self.transport = None
    
    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        self.transport = transport
        self.transport.write(json.dumps({ 'init_data':self.editor.data }).encode())

    def data_received(self, data):
        msg = data.decode()
        self.editor.on_data_received(msg)

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        if self.transport and self.editor.should_broadcast_edit(data['key_code']):
            self.transport.write(json.dumps(data).encode())
        self.editor.handle_key_code(data['key_code'], data['x'], data['y'])

    def set_editor(self, editor):
        self.editor = editor

    def init_editor(self):
        self.editor.init()

def main(stdscr):
    stdscr.clear()
    
    fname = "test.py"
    editor = Editor(stdscr, fname)
    
    loop = asyncio.get_event_loop()
    protocol = EchoServerClientProtocol()
    protocol.set_editor(editor)
    protocol.init_editor()
    loop.add_reader(sys.stdin, got_stdin_data, protocol)

    # Each client connection will create a new protocol instance
    coro = loop.create_server(lambda: protocol, '127.0.0.1', 8888)
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
    curses.wrapper(main)

