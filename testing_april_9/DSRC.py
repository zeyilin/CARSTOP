# -*- coding: utf-8 -*-
"""
last mod 4/8/17
"""
import time
from multiprocessing import Process
from connectors import RxConnector

def parsemessage(message):
    msg = message.split('\n')
    if msg[0][4]=='R':
        Rx = 1
    elif msg[0][4]=='T':
        Rx = 0
    else:
        assert False, "not reading Tx/Rx right, "+msg[0]
    important_part = ' '.join(msg[4:7])
    message_bytes = important_part.split()
    raw_message = [Rx, # 1 received msg, 0 sent msg
                hex_to_uint(message_bytes[0]), # msg_id
                hex_to_uint(''.join(message_bytes[1:5])), # tmp id
                hex_to_uint(''.join(message_bytes[5:7])), # 2 byte current seconds
                hex_to_int(''.join(message_bytes[7:11]), 32), # 4 byte lat
                hex_to_int(''.join(message_bytes[11:15]), 32), # 4 byte long
                hex_to_int(''.join(message_bytes[15:17]), 16), # 2 byte elevation
                hex_to_uint(''.join(message_bytes[17:21]))] # 4 byte accuracy
    #extra_message = ''.join((chr(hex_to_uint(h)) for h in message_bytes[38:54]))
    extra_message = '' # only because this DSRC (115.37) is out of date!
    return (raw_message, extra_message)
def hex_to_uint(h):
    return int(h, 16)  
def hex_to_int(h, d):
    i = int(h, 16)
    if i >= 2**(d-1): i -= 2**d
    return i

class DsrcLog(Process):
    def __init__(self, port, filename, waitOnStart=False):
        self.conn = RxConnector(port, 'UDP')
        self.log = open(filename, 'w')
        header = 'rcv_time,rcv,msg_id,tmp_id,snd_time,lat,lon,elevation,accuracy'
        self.log.write(header)
        self.wait = waitOnStart
        Process.__init__(self)
        
    def start(self, referenceTime):
        self.startTime = referenceTime
        if self.wait:
            self.conn.recv(1024) # wait until you receive first message
        Process.start(self)
        
    def run(self):
        while True:
            news = self.conn.recv(1024, .2)
            assert news!='', "DSRC connection stopped"
            bsm, extra = parsemessage(news)
            rcv_time = '\n{:9.3f},'.format(time.time() - self.startTime)
            self.log.write(rcv_time + ','.join((str(mm) for mm in bsm)) )
            
    def __enter__(self): return self
    def __exit__(self, errtype, errval, traceback):
        self.log.close()
        self.conn.__exit__(errtype, errval, traceback)
        Process.terminate(self)
