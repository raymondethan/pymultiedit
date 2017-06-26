from __future__ import print_function
import asyncio
import logging
import socket
import struct
from random import random
import sys
import json
import curses
from editor import Editor
from constants import *

BROADCAST_PORT = 9999
BROADCAST_ADDR = "228.0.0.5"
addr_info = (BROADCAST_ADDR, BROADCAST_PORT)
myid = random()

def got_stdin_data(protocol):
    data = protocol.editor.screen.getch()
    msg = json.dumps({ KEY_CODE: data, KEY_X:None, KEY_Y:None })
    protocol.user_input_received(msg)

class MulticastServerProtocol(asyncio.Protocol):

    def __init__(self, _id, editor):
        self._id = _id
        self.editor = editor

    def connection_made(self, transport):
        self.transport = transport
        msg = json.dumps({'id':myid, 'cmd':'start'})
        self.transport.sendto(msg.encode(), addr_info)

    def datagram_received(self, data, addr):
        data = json.loads(data.decode())
        
        print("Datagram %s received from %s" % (repr(data), repr(addr)))
        if data['id'] == myid: return
        
        if 'cmd' in data and data['cmd'] == 'start':
            msg = json.dumps({ KEY_ID:myid, KEY_INIT: self.editor.data })
            self.transport.sendto(msg.encode(), addr_info)
        if KEY_INIT in data:
            self.editor.data = data[KEY_INIT]
            self.editor.display()
            #print('my new data',self.editor.data)
        else: 
            self.editor.on_data_received(json.dumps(data))
            #print('makng edits now!!!!!')

    def user_input_received(self, msg):
        data = self.editor.parse_input_data(msg)
        data[KEY_ID] = self._id
        if self.editor.should_broadcast_edit(data[KEY_CODE]):
            self.transport.sendto(json.dumps(data).encode(), addr_info)
        self.editor.handle_key_code(data[KEY_CODE], data[KEY_X], data[KEY_Y])

    def set_editor(self, editor):
        self.editor = editor

    def init_editor(self):
        self.editor.init()


def main(stdscr):

    stdscr.clear()
    fname = sys.argv[1] if len(sys.argv) > 1 else None
    editor = Editor(stdscr, fname)
    
    loop = asyncio.get_event_loop()
    #print("My id:",myid)
    #loop.set_debug(True)
    logging.basicConfig(level=logging.DEBUG)
    
    protocol =  MulticastServerProtocol(myid, editor)
    protocol.init_editor()
    loop.add_reader(sys.stdin, got_stdin_data, protocol)
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', BROADCAST_PORT))
    group = socket.inet_aton(BROADCAST_ADDR)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)

    listen = loop.create_datagram_endpoint(
        lambda: protocol,
        sock=sock,
    )
    loop.add_reader(sys.stdin, got_stdin_data, protocol)
    transport, protocol = loop.run_until_complete(listen)

    loop.run_forever()
    loop.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Need to specify a file name') 
        sys.exit()
    curses.wrapper(main)
