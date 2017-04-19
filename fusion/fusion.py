#----------Set path for module import--------#
import sys, os
path = os.path.realpath(__file__)
path, directory = os.path.split(path)
path, directory = os.path.split(path)
sys.path.append(path)
#----------Set path for module import--------#

import cv2, connectors, time
from io import BytesIO
from struct import unpack
from radar.test_radar import Radar

print_timing = True
cam_res = (1280,720)
fps = 10 # frames per second
IP = '127.0.0.1' #'192.168.0.138' #
DESTPORT = 9002


class Detected_Object():
    def __init__(self, packet):
        (self.x, self.y, self.h, self.w, classification, self.prob) = unpack('iiiiif', packet[4:])
        if(classification == 0):
            self.classification = 'pedestrian'
        elif(classification == 1):
            self.classification = 'bicycle'
        elif(classification == 52):
            self.classification = 'hotdog'
        elif(classification == 2 or classification == 3 or classification == 5 or classification == 7):
            self.classification = 'motorvehicle'
        else:
            self.classifcation = 'unknown'
        
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

def get_packet(tx):
    while(True):
        try:
            packet = tx.recv(28)
            return packet
        except Exception as e:
            pass

def get_detected_objects_packets(tx):
    objects = []
    packet = get_packet(tx)
    eof, = unpack('i', packet[0:4])

    while(len(packet) == 28 and eof == 0):
        objects.append(Detected_Object(packet))
        packet = get_packet(tx)
        eof, = unpack('i', packet[0:4])

    return objects

def draw_detected_objects(frame, objects):
    for obj in objects:
        if(obj.classification == 'pedestrian'):
            cv2.rectangle(frame, (obj.x, obj.y), (obj.x+obj.w, obj.y+obj.h), (0, 0, 204), 2)
        elif(obj.classification == 'bicycle'):
            cv2.rectangle(frame, (obj.x, obj.y), (obj.x+obj.w, obj.y+obj.h), (204,0, 0), 2)
        elif(obj.classification == 'hotdog'):
            cv2.rectangle(frame, (obj.x, obj.y), (obj.x+obj.w, obj.y+obj.h), (102, 0, 255), 2)
        elif(obj.classification == 'motorvehicle'):
            cv2.rectangle(frame, (obj.x, obj.y), (obj.x+obj.w, obj.y+obj.h), (204,0, 153), 2)
        else:
            #unknown classification
            cv2.rectangle(frame, (obj.x, obj.y), (obj.x+obj.w, obj.y+obj.h), (0,204, 0), 2)

def test_stream():
    cam = Camera(0)

    with cam:
        while True:
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
            tx.send(io_obj.getvalue())
            io_obj.close()
            time.sleep(.05)

def test_demo():
    cam = Camera(0)

    tx = connectors.ClientConnector(IP, DESTPORT, 'TCP')
    tx.s.settimeout(1)

    frame = cam.read()

    io_obj = BytesIO(frame.flatten())
    tx.send(io_obj.getvalue())
    io_obj.close()

    r = Radar("test.csv")
    r.init()
    thresh = .01
    with tx, cam:
        while(True):
            frame = cam.read()
            radar_data = None
            while r.not_empty():
                radar_data = r.get()

            io_obj = BytesIO(frame.flatten())
            tx.send(io_obj.getvalue())
            io_obj.close()

            objects = get_detected_objects_packets(tx)
            draw_detected_objects(frame, objects)
            print('Detected {} Objects'.format(len(objects)))
            cv2.imshow('frame', frame)
            cv2.waitKey(1)
            names = ['r' + str(n) for n in range(len(radar_data))]
            scores = pd.DataFrame(columns=names)
            for index in range(len(objects)):
                box_scores = []
                yolo_coords = (objects[index].x, objects[index].x + objects[index].w)
                for ind, radar_box in radar_data.iterrows():
                    sum_lengths = yolo_coords[1] - yolo_coords[0] - radar_box['left_pixel'] + radar_box['right_pixel']
                    overlap = -max(yolo_coords[0], radar_box['left_pixel']) + min(yolo_coords[1], radar_box['right_pixel'])
                    box_scores.append(overlap/sum_lengths)
                scores.loc[index] = box_scores
            matches = []
            filtered_df = radar_data.copy()
            for yolo_object in range(len(radar_data)):
                best_score = None
                best_score_coords = None
                for i, row in scores.iterrows():
                    if row.max() > best_score:
                        best_score_coords = (i, row.idxmax())
                if best_score < thresh:
                    break
                matches.append((yolo_object, best_score_coords[1]))
                filtered_df.drop(best_score_coords[0], axis=0)
                filtered_df.drop(best_score_coords[1], axis=1)

            time.sleep(.05)
                

if __name__ == '__main__':
    test_demo()
