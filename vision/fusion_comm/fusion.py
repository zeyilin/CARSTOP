
print_timing = True
cam_res = (1280,720)
fps = 10 # frames per second
IP = '127.0.0.1' #'192.168.0.138' #
DESTPORT = 9002

import cv2, connectors, time
from io import BytesIO
import numpy as np
import binascii
from struct import unpack

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

def main():    
    cam = Camera(0)

    tx = connectors.TxConnector(IP, DESTPORT, 'TCP')

    count = 0
    time.sleep(.1)
    firsttime = time.time()

    with tx, cam:
        while True:
            frame = cam.read()
            cv2.imshow('Frame', frame)
            continue

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

def test_stream():
    cam = Camera(0)

    count = 0
    time.sleep(.1)
    firsttime = time.time()

    with cam:
        while True:
            print('hello')
            frame = cam.read()
            cv2.imshow('frame', frame)
            cv2.waitKey(1)

def test_send():
    cam = Camera(0)

    tx = connectors.ClientConnector(IP, DESTPORT, 'TCP')

    with tx, cam:
        while True:
            frame = cam.read()
            io_obj = BytesIO(frame.flatten())
            t = time.time()
            tx.send(io_obj.getvalue())
            print('Round trip time = {}'.format(time.time()-t))
            io_obj.close()
            time.sleep(.05)

def get_packet(tx):
    while(True):
        try:
            packet = tx.recv(28)
            print("Received packet: {}".format(binascii.b2a_hex(packet)))
            print("Received packet of length: {}".format(len(packet)))
            return packet
        except Exception as e:
            pass

def get_detected_objects_packets(tx):
    data = ''
    packet = binascii.b2a_hex(get_packet(tx))

    while(len(packet) > 0 and packet[0:2] == '00'):
        data += packet
        packet = binascii.b2a_hex(get_packet(tx))

    print('Received data of length: {}'.format(len(data)))
    print('Data contents in hex: {}'.format(data))
    return data

def test_sendrecv():
    cam = Camera(0)

    tx = connectors.ClientConnector(IP, DESTPORT, 'TCP')
    tx.s.settimeout(1)

    frame = cam.read()

    io_obj = BytesIO(frame.flatten())
    tx.send(io_obj.getvalue())
    io_obj.close()

    with tx, cam:
        while(True):
            frame = cam.read()

            io_obj = BytesIO(frame.flatten())
            tx.send(io_obj.getvalue())
            io_obj.close()

            packets = get_detected_objects_packets(tx)


            time.sleep(.05)
                

if __name__ == '__main__':
    test_sendrecv()


#capture image
	# testmmwv_to_darknet.py


#send image to darkent
	# testmmwv_to_darknet.py



#receive image in darknet
	# recvmmwv = 1 in darknet



#send detected objects from darknet
	# senddsrc = 1 in darknet

#receive detected objects
	# TODO make a receiving script

#output detected objects
	# TODO make an outputting script

