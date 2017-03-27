#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
last mod 3/15/17
"""

YOLO_maxwaittime = .1
YOLO_port = 9002
IM_SIZE = (720,1280)


import connectors, time
import numpy as np
import cv2

data = ''
frame = np.empty((IM_SIZE[0],IM_SIZE[1],3), dtype='uint8')
ff = IM_SIZE[0]*IM_SIZE[1]
msg_size = IM_SIZE[0]*IM_SIZE[1]*3


with connectors.RxConnector(YOLO_port) as rx:
    while True:
        while len(data) < msg_size:
            data += rx.recv(4096)
        rx.ack()
        darray = np.fromstring(data[:msg_size], 'u1')
        frame[:,:,2] = darray[:ff].reshape(IM_SIZE)
        frame[:,:,1] = darray[ff:ff*2].reshape(IM_SIZE)
        frame[:,:,0] = darray[ff*2:].reshape(IM_SIZE)
        
        data = data[msg_size:]
        
        cv2.imshow('ITX View',frame)
        cv2.waitKey(1)

cv2.destroyAllWindows()