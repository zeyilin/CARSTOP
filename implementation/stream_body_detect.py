import numpy as np
import cv2
from imutils.object_detection import non_max_suppression

def determine_distance(image_height, object_y):
        # print('Image Height = {}'.format(image_height))
        delta = image_height - object_y
        # print('Distance = {}'.format(delta))
        percdelta = (100*delta) / image_height
        # print('Percentage Distance = {}%'.format(percdelta))
        if(percdelta <= 10):
            dist = 10 
        elif(percdelta > 10 and percdelta <= 15):
            dist = 15 
        elif(percdelta > 15 and percdelta <= 20):
            dist = 20   
        elif(percdelta > 20 and percdelta <= 25):
            dist = 25   
        elif(percdelta > 25 and percdelta <= 30):
            dist = 30   
        elif(percdelta > 30 and percdelta <= 50):
            dist = 35  
        else:
            dist = 40
        return dist

def side_alert(image_w, object_x):
    if(image_w/4 > object_x):
        return 'Left Alert'
    elif((3*image_w)/4 < object_x):
        return 'Right Alert'
    else:
        return None

if __name__ == '__main__':

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector( cv2.HOGDescriptor_getDefaultPeopleDetector() )
    cap=cv2.VideoCapture('videos/video1.mov')
    # cap=cv2.VideoCapture(0)
    print('STARTING')
    while True:
        ret,frame=cap.read()
        frame_width = frame.shape[1]
        frame_height = frame.shape[0]
        if not ret: continue
        rects,w=hog.detectMultiScale(frame, winStride=(8,8), padding=(32,32), scale=1.05)

        #non-maximal suppression
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        sup_rects = non_max_suppression(rects, probs=None, overlapThresh=0.65)

        # draw the final bounding boxes
        for (x0, y0, x1, y1) in sup_rects:
            cv2.rectangle(frame, (x0, y0), (x1, y1), (0, 255, 0), 2) 
            dist = determine_distance(frame_height, y1)
            text = '{}ft'.format(dist)
            cv2.putText(frame, text, org=(x0,y0), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.5, color=(255,0,0), thickness=2)
            object_x = (x0+x1)/2
            alert = side_alert(frame_width, object_x)
            if alert:
                cv2.putText(frame, alert, org=(x0,y0+15), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                            fontScale=0.5, color=(0,0,255), thickness=2)

        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xff == ord('q'):
            break
    cv2.destroyAllWindows()