# -*- coding: utf-8 -*-
"""
last update 2/20/17
"""

import socket, time, select
DSRC_maxwaittime = .1 # s
DSRC_rxport = 9001
DSRC_txport = 9001

class RxSocket():
    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.s.bind(('',port))
        self.firsttime = True
        print("DSRC Rx waiting")
	
    def recv(self, size):	
        if self.firsttime: # make sure the receive doesn't block
            readable,a,b = select.select([rxsock.s], [], [], 20.)
            if len(readable) == 0:
                print("timed out without ever receiving a message")
                return ''
            print("DSRC Rx receiving")
            self.firsttime = False
        else:
            readable,a,b = select.select([rxsock.s], [], [], DSRC_maxwaittime)
            if len(readable)==0:
                print("timed out")
                return ''
        return rxsock.s.recv(size)
    
    def __enter__(self):
        return self
    def __exit__(self, errtype, errval, traceback):
        self.s.close()

		
## sends extra info to the DSRC to be broadcast
## right now you can only send 16 bytes of data for each message
class TxSocket():
    def __init__(self, ip, port):
		# create a UDP sender
        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.ip = ip
        self.port = port
        
    def send(self, msg):
        self.s.sendto(msg, (self.ip, self.port))
    
    def __enter__(self):
        return self
    def __exit__(self, errtype, errval, traceback):
        self.s.close()
        
		
def hex_to_int(h, d):
    i = int(h, 16)
    if i >= 2**(d-1):
        i -= 2**d
    return i
def hex_to_uint(h):
    return int(h, 16)    
    
def parsemessage(message):
    important_part = ' '.join(message.split('\n')[4:7])
    message_bytes = important_part.split()
    raw_message = [hex_to_uint(message_bytes[0]), # msg_id
                hex_to_uint(''.join(message_bytes[1:5])), # tmp id
                hex_to_uint(''.join(message_bytes[5:7])), # 2 byte current seconds
                hex_to_int(''.join(message_bytes[7:11]), 32), # 4 byte lat
                hex_to_int(''.join(message_bytes[11:15]), 32), # 4 byte long
                hex_to_int(''.join(message_bytes[15:17]), 16), # 2 byte elevation
                hex_to_uint(''.join(message_bytes[17:21]))] # 4 byte accuracy
    extra_message = ''.join((chr(hex_to_uint(h)) for h in message_bytes[38:54]))
    return (raw_message, extra_message)
		
		
firsttime = True
lasttime = time.time()
with open('bsmoutfile.dat', 'w') as logfile, RxSocket(DSRC_rxport) as rxsock,\
         TxSocket('169.254.113.221',DSRC_txport) as txsock:
    while True:
        news = rxsock.recv(1024) # power of 2 large enough for whole message
        if news == '':
            print("socket closed")
            break
        #bsm, extra = parsemessage(news)
        #logfile.write(str(bsm) + ';' + extra + '\n')
        logfile.write(news)
        thistime = time.time()
        if thistime - lasttime > .1:    
            txsock.send(u'ABCDEFGHIJKLMNOP')
            lasttime = thistime