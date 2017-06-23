from __future__ import print_function
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
import curses
import json
from random import random
from editor import Editor
from constants import *

group = "228.0.0.5"
addr_info = (group, 9999)
myid = random()

class MulticastPingClient(DatagramProtocol):

    def startProtocol(self):
        # Join the multicast address, so we can receive replies:
        self.transport.setTTL(1)
        self.transport.joinGroup(group)
        # (including us) will receive this message.
        msg = json.dumps({'id':myid, 'cmd':'start'})
        self.transport.write(msg.encode(), addr_info)

    def datagramReceived(self, datagram, address):
        datagram = json.loads(datagram.decode())
        
        print("Datagram %s received from %s" % (repr(datagram), repr(address)))
        if datagram['id'] == myid: return
        
        if 'cmd' in datagram and datagram['cmd'] == 'start':
            msg = json.dumps({ KEY_ID:myid, KEY_INIT: ['this','is','my','data'] })
            self.transport.write(msg.encode(), addr_info)
        if KEY_INIT in datagram:
            self.data = datagram[KEY_INIT]
            print('my new data',self.data)
        else: 
            #self.editor.on_data_received(json.dumps(msg))
            print('makng edits now!!!!!')

def main(stdscr):
    #stdscr.clear()
    
    fname = "test.py"
    #editor = Editor(stdscr, fname)
    print("My id:",myid)
    print("\n")
    
    reactor.listenMulticast(9999, MulticastPingClient(), listenMultiple=True)
    reactor.run()

if __name__ == '__main__':
    #curses.wrapper(main)
    main(None)
