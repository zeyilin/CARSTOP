#!/usr/bin/env python2
# -*- coding: utf-8 -*-
from multiprocessing import Process
import sys, time
import canlib
import numpy as np
from sys import platform


""" This is a shortened version of the code used by last year's senior design
team. I imagine they got the original from Delphi or AutonomouStuff at some point.
The code has been shortened to only gather object location information, 
namely range, angle, range rate (speed toward/from self) and lateral rate"""
class Radar(Process):
    """ Listens for new Radar messages over CAN and parses for the dispatcher.

    This parser reads messages from the CAN Bus using the Kvaser USB Python SKD
    and formats Radar information into a python object. Then we send the data
    along to the event dispatcher.
    """
    def __init__(self, filename):
        """ Initialize the data parser, connect to the can bus. """
        Process.__init__(self)
        self.data = {}
        self.power_tracks = {}
        self.file = open('filename','w')
        self.startTime = None
        
        cl = canlib.canlib()
        self.ch1 = cl.openChannel(0, canlib.canOPEN_ACCEPT_VIRTUAL)
        
    def start(self, referenceTime):
        self.startTime = referenceTime
        Process.start(self)

    def run(self):

        try:
            print("Using channel: %s, EAN: %s" % (
                self.ch1.getChannelData_Name(), self.ch1.getChannelData_EAN()))

            self.ch1.setBusOutputControl(canlib.canDRIVER_NORMAL)
            self.ch1.setBusParams(canlib.canBITRATE_500K)
            self.ch1.busOn()
        except (canlib.canError) as ex:
            print(ex)

        # Initialize the Radar
        message = [0,0,0,0,0,0,191,0]
        self.ch1.write(1265,message,8)

        msg_counter = 0 # Variable that keeps track of the iteration of msg 1344 we are on
        
        while True:
            ss = time.time() #- self.startTime
            try:
                msgId, msg, dlc, flg, msgtime = self.ch1.read()

                if msgId >= 1280 and msgId <= 1343:
                    self.track_msg(msgId, msg)
                elif (msgId == 1344):
                    self.track_status_msg(msg_counter, msg)
                    msg_counter += 1
                elif (msgId > 1344 and msg_counter > 0):
                    msg_counter = 0
                elif (msgId == 1512):
                    sdat = [(ss,k,v[0],v[1],v[2],v[3],self.power_tracks[k])
                            for k,v in self.data.iteritems()
                            if self.power_tracks[k] > 0]
                    self.file.write('\n'+array2str(sdat))
                    self.data = {} # Start with a fresh object
                    self.power_tracks  = {}
            except (canlib.canNoMsg) as ex:
                pass
            except (canlib.canError) as ex:
                print(ex)

    def track_msg(self, msgId, msg):
        """ message ID 500-53F or 1280-1343 """
        track_id = str(msgId-1279)
        status = ((msg[1] & 0xE0) >> 5)
        if (status < 2 or status > 3):
            return
        radarrange = (((msg[2] & 0x07) << 8) | msg[3]) / 10.0
        angle = (((msg[1] & 0x1F) << 5) | ((msg[2] & 0xF8) >> 3))
        angle = hex_to_int(angle, 10) / 10.0
        range_rate = (((msg[6] & 0x3F) << 8) | msg[7])
        range_rate = hex_to_int(range_rate, 14) / 100.0
        lat_rate = ((msg[0] & 0xFC) >> 2)
        lat_rate = hex_to_int(lat_rate, 6) / 4.0
        self.data[track_id]  = (radarrange, angle, range_rate, lat_rate)

    def track_status_msg(self, msg_counter, msg):
        """ message ID x540 or 1344 """
        for i in range(1, 8):
            track_id = str((msg_counter*7)+i)
            track_power = (msg[i] & 0x1F)
            self.power_tracks[track_id] = track_power
            if ((msg_counter*7)+i) >= 64:
                break
    
    def terminate(self):
        self.file.close()
        self.ch1.busOff()
        Process.terminate(self)
    
    def __enter__(self): return self
    def __exit__(self, errtype, errval, traceback):
        if Process.is_alive(self): self.terminate()

def hex_to_int(h, d):
    # h = number to convert (can be integer)
    # d = number of bits in the number
    i = h
    if i >= 2**(d-1):
        i -= 2**d
    return i
        
# converts a 2D array to a csv string
def array2str(array):
    return '\n'.join((','.join((str(ele) for ele in row)) for row in array))
