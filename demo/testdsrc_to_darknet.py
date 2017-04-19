#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
last update 3/14/17
"""
interval = 2. # s, time to wait before changing vehicle states
YOLO_minwaittime = .1 # s, time to wait before sending next box to darknet
YOLO_port = 9002

ANGLE = -45. # the car's N-S/E-W angle, you have to handcode this
VIEW = 45. # field of view of the camera
FRAME = (1280,720)

bsms = [[1,2,2],[1,6,1],[1,6,-1],[1,6,-5], [1,5,-6]]


import connectors, time, sys, utm
import numpy as np      

# latitude and longitude to UTM   
def convertCoords(lat, lon):
    if lat >= 90. or lat == 0.: # measurements not taken
        return (0., 0.)
    return utm.from_latlon(lat, lon)[:2]


""" better """
def updatePositions(x1, y1, x2, y2, msg):
    x,y = (msg[1],msg[2])#convertCoords(msg[1], msg[2])
    if msg[0] == 1:
        return (x1, y1, x, y)
    else:
        return (x, y, x2, y2)

""" locate vehicle's relative position, send to YOLO in message format """
def decideOutput(x1, y1, x2, y2):
    x = x2 - x1
    y = y2 - y1
    d = (x**2 + y**2)**.5
    
    ang = np.arctan2(y, x) * 180. / np.pi
    ang = ANGLE - ang
    if ang > 180: ang -= 360
    if ang < -180: ang += 360
    
    if ang > VIEW and ang <= 80:
        return 'RU0000000'
    elif ang < -VIEW and ang >= -80:
        return 'LU0000000'
    elif ang > 80 and ang <= 120:
        return 'RC0000000'
    elif ang < -80 and ang >= -120:
        return 'LC0000000'
    elif ang > 120:
        return 'RB0000000'
    elif ang < -120:
        return 'LB0000000'
    else:
        # find pixels for box corners
        center = (1. + ang/VIEW)*FRAME[0]/2
        size = max((20. - d), 1) *FRAME[1]/100
        h1 = max(0, center - size)
        h2 = min(FRAME[0], center + size)
        v1 = max(0, FRAME[1] * .5 - size)
        v2 = min(FRAME[1], FRAME[1] * .5 + size)
        #print ' '.join(('C',str(h1),str(h2),str(v1),str(v2)))
        # convert to byte message
        h1a = chr(int(h1) / 256)
        h1b = chr(int(h1) % 256)
        h2a = chr(int(h2) / 256)
        h2b = chr(int(h2) % 256)
        v1a = chr(int(v1) / 256)
        v1b = chr(int(v1) % 256)
        v2a = chr(int(v2) / 256)
        v2b = chr(int(v2) % 256)
        return ''.join(('C',h1a,h1b,h2a,h2b,v1a,v1b,v2a,v2b))
        

## main code here
x1, y1, x2, y2 = (0.,0.,1.,1.)
firsttime = True
lasttime = time.time()
lastintvl = lasttime
i = 0;

with connectors.TxConnector("",YOLO_port) as txsock:
    while True:
        time.sleep(.02)
        thistime = time.time()
        if thistime - lasttime > YOLO_minwaittime:
            msg = decideOutput(x1,y1,x2,y2)
            txsock.send(msg)
            lasttime = thistime
        if thistime - lastintvl > interval:
            print bsms[i]
            x1,y1,x2,y2 = updatePositions(x1,y1,x2,y2, bsms[i])
            lastintvl = thistime
            i += 1
            if i >= len(bsms):
                i = 0