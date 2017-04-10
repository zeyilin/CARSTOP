# -*- coding: utf-8 -*-
"""
last mod 3/14/17
"""

communicate = False # only set to False for testing camera
print_timing = True
cam_res = (1280,720)
fps = 10 # frames per second
IP = '127.0.0.1' #'192.168.0.138' #
PORT = 9002

import cv2, connectors, time
from io import BytesIO
import numpy as np

class Camera():
    def __init__(self, capnum):
        self.cap = cv2.VideoCapture(capnum)
        self.cap.set(cv2.CAP_PROP_FPS, fps)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,cam_res[0])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT,cam_res[1])
        time.sleep(.1)
        ret, frame = self.cap.read()
        assert ret # check the camera's functionality with a single snapshot
        print "connected to camera"
        
    def read(self):
        ret, frame = self.cap.read()
        return frame
    
    def __enter__(self): return self
    def __exit__(self, errtype, errval, traceback):
        self.cap.release()
        
cam = Camera(0)

# start up socket
if communicate:
    # PORT = int(raw_input("type the port number: "))
    tx = connectors.TxConnector(IP, PORT, 'TCP')
else:
    tx = connectors.NullConnector()

count = 0
time.sleep(.1)
firsttime = time.time()

with tx, cam:
    while True:
        frame = cam.read()
        msgtime = time.time()
        
        io_obj = BytesIO(frame.flatten())
        tx.send(io_obj.getvalue())
        tx.ack()
        io_obj.close()
        time.sleep(.05)
            
        gap = time.time() - msgtime
        if print_timing:
            print "{:.2f}".format(msgtime - firsttime)
            print "runtime {:.3f}".format(gap)