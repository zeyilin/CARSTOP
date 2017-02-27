#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
last mod 12/21/16
"""

from multiprocessing import Process, Queue
import sys, time

import canlib
import numpy as np
from radar_GFM import RadarGFM
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.animation as manimation
from sys import platform

FPS = 5
cam_res = (1920, 1080) # (1280, 720) #
estimated_delay = .05 # expected length in seconds of each step


""" This is a shortened version of the code used by last year's senior design
team. I imagine they got the original from Delphi or AutonomouStuff at some point.
The code has been shortened to only gather object location information, 
namely range, angle, range rate (speed toward/from self) and lateral rate"""
class RadarParser(Process):
    """ Listens for new Radar messages over CAN and parses for the dispatcher.

    This parser reads messages from the CAN Bus using the Kvaser USB Python SKD
    and formats Radar information into a python object. Then we send the data
    along to the event dispatcher.
    """
    def __init__(self, queue):
        """ Initialize the data parser, connect to the can bus. """
        Process.__init__(self)
        self.data = {}
        self.power_tracks = {}
        self.queue = queue
        self.startTime = None
        
    def start(self, referenceTime):
        self.startTime = referenceTime
        Process.start(self)

    def run(self):
        cl = canlib.canlib()
        channels = cl.getNumberOfChannels()
        ch = 0; # Hard-coded, might need to change!
        if ch >= channels:
            print("Invalid channel number")
            sys.exit()

        try:
            ch1 = cl.openChannel(ch, canlib.canOPEN_ACCEPT_VIRTUAL)
            print("Using channel: %s, EAN: %s" % (ch1.getChannelData_Name(),
            ch1.getChannelData_EAN()))

            ch1.setBusOutputControl(canlib.canDRIVER_NORMAL)
            ch1.setBusParams(canlib.canBITRATE_500K)
            ch1.busOn()
        except (canlib.canError) as ex:
            print(ex)

        # Initialize the Radar
        message = [0,0,0,0,0,0,191,0]
        ch1.write(1265,message,8)

        msg_counter = 0 # Variable that keeps track of the iteration of msg 1344 we are on
        
        while True:
            ss = time.time() - self.startTime
            try:
                msgId, msg, dlc, flg, msgtime = ch1.read()

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
                    self.queue.put(sdat)
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
        angle = self.hex_to_int(angle, 10) / 10.0
        range_rate = (((msg[6] & 0x3F) << 8) | msg[7])
        range_rate = self.hex_to_int(range_rate, 14) / 100.0
        lat_rate = ((msg[0] & 0xFC) >> 2)
        lat_rate = self.hex_to_int(lat_rate, 6) / 4.0
        self.data[track_id]  = (radarrange, angle, range_rate, lat_rate)

    def track_status_msg(self, msg_counter, msg):
        """ message ID x540 or 1344 """
        for i in range(1, 8):
            track_id = str((msg_counter*7)+i)
            track_power = (msg[i] & 0x1F)
            self.power_tracks[track_id] = track_power
            if ((msg_counter*7)+i) >= 64:
                break
    
    def hex_to_int(self, h, d):
        # h = number to convert (can be integer)
        # d = number of bits in the number
        i = h
        if i >= 2**(d-1):
            i -= 2**d
        return i

        
# converts a 2D array to a csv string
def array2str(array):
    return '\n'.join((','.join((str(ele) for ele in row)) for row in array))

"""
Saves video files using matplotlib - this is much slower than
OpenCV's video code, but is the only code that currently works on Windows.
"""
class MPL_VideoWriter():
    def __init__(self, filename, cam_res, fps):
        figwidth = 10 # inches, must be a factor of frame width and height
        fig = plt.figure(dpi = cam_res[0]/figwidth,
                         figsize=(figwidth, cam_res[1]/float(cam_res[0])*figwidth))
        ax = plt.Axes(fig, [0., 0., 1., 1.])
        ax.set_axis_off()
        fig.add_axes(ax)
        self.aplt = plt.imshow(np.zeros((cam_res[1],cam_res[0],3),dtype=np.uint8)
                            *255, aspect='equal',interpolation='none')
        self.writer = manimation.FFMpegWriter(fps=fps, bitrate=250*fps)
        self.writer.setup(fig, filename, fig.dpi)
    def __enter__(self):
        return self
    def __exit__(self, errtype, errval, traceback):
        self.writer.finish()
        self.writer.cleanup()
    def write(self, image):
        self.aplt.set_data(image[:,:,::-1])
        self.writer.grab_frame()
       
""" Saves video files using OpenCV """
class OCV_VideoWriter():
    def __init__(self, filename, cam_res, fps):
        if platform == 'linux' or platform == 'linux2':
            codec = 'FMP4'
            filename = filename[:-4]+'.avi'
        else:
            codec = 'MP4V'
        if cv2.__version__[0] == '2':
            fourcc = cv2.cv.CV_FOURCC(*codec)
        else:
            fourcc = cv2.VideoWriter_fourcc(*codec)
        self.writer = cv2.VideoWriter(filename, fourcc, fps, cam_res)
    def __enter__(self):
        assert self.writer.isOpened()
        return self
    def __exit__(self, errtype, errval, traceback):
        self.writer.release()
    def write(self, image):
        self.writer.write(image)
        
        
""" Captures images directly from a camera using OpenCV """
class VideoCapture():
    def __init__(self, fps, cam_res):
        self.cap = cv2.VideoCapture(0)
        if cv2.__version__[0] == '2':
            self.cap.set(cv2.cv.CV_CAP_PROP_FPS, fps)
            self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH,cam_res[0])
            self.cap.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT,cam_res[1])
        else:
            self.cap.set(cv2.CAP_PROP_FPS, fps)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,cam_res[0])
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cam_res[1])
    def __enter__(self):
        ret, frame = self.cap.read()
        assert ret
        return self
    def read(self):
        ret, frame = self.cap.read()
        return frame
    def __exit__(self, errtype, errval, traceback):
        self.cap.release()
    

""" stores the starting time, ending time, and ending status for any test """
class BasicLog():
    def __init__(self, filename):
        self.fil = open(filename, 'w+')
    def __enter__(self):
        return self
    def start(self, stime):
        timestring = '{}, {:.0f}'.format(time.ctime(int(stime)), stime%1*1000)+' ms'
        self.fil.write("start = "+timestring)
    def __exit__(self, errtype, errval, traceback):
        stime = time.time()
        timestring = '{}, {:.0f}'.format(time.ctime(int(stime)), stime%1*1000)+' ms'
        self.fil.write('\n end = '+timestring)
        if errtype == KeyboardInterrupt:
            self.fil.write('\n natural exit')
        else:
            self.fil.write(str(traceback))
            print errval
        self.fil.close()
        
        
''' This is a basic class that lets you put a Process in a *with* statement.
At the end of the with statement (including error) it ends the process. '''
class ProcessProtector():
    def __init__(self, process): self.proc = process
    def __enter__(self): pass
    def __exit__(self, errtype, errval, traceback):
        if self.proc.is_alive(): self.proc.terminate()
        
        
if __name__ == '__main__':
    radarQueue = Queue()
    radarInterface = RadarParser(radarQueue)
    GFM = RadarGFM()
    
    with  BasicLog("basic_details.txt") as basiclog ,\
          open("radar_preGFM.txt", 'w') as logfile_pre ,\
          open("radar_postGFM.txt", 'w') as logfile_post ,\
          VideoCapture(FPS, cam_res) as cap0 ,\
          OCV_VideoWriter("camera.mp4", cam_res, FPS) as videowriter ,\
          ProcessProtector(radarInterface):
        logfile_pre.write('time,track,range,angle,rangerate,latrate,power')
        logfile_post.write('time,range,angle')
            
        radarStartTime = time.time()
        radarInterface.start(radarStartTime)
        basiclog.start(radarStartTime)
        #assert radarInterface.is_alive()
            
        while True:
            time.sleep(1./FPS - estimated_delay)
            ss = time.time()
            while not radarQueue.empty():
                nextradarmessages = radarQueue.get()
                logfile_pre.write('\n'+array2str(nextradarmessages))
                for nextmessage in nextradarmessages: GFM.update(nextmessage)
            t1 = time.time()
            dt1 = t1 - ss
            output = GFM.output(ss - radarStartTime)
            logfile_post.write('\n'+str(ss - radarStartTime))
            logfile_post.write('\n'+array2str(output))
            t2 = time.time()
            dt2 = t2-t1
            
            ret, frame = cap0.cap.read()
            t3 = time.time()
            dt3 = t3 - t2
            videowriter.write(frame)
            dt4 = time.time() - t3
            print "times {:.3f}, {:.3f}, {:.3f}, {:.3f}".format(dt1,dt2,dt3,dt4)