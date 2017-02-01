import numpy as np
import cv2
from imutils.object_detection import non_max_suppression

def determine_distance(image_height, object_y, object_h):
        # print('Image Height = {}'.format(image_height))
        delta = image_height-(object_y+object_h)
        # print('Distance = {}'.format(delta))
        percdelta = (100*delta) / image_height
        # print('Percentage Distance = {}%'.format(percdelta))
        if(percdelta <= 10):
            dist = 10 
        elif(percdelta > 10 and percdelta <= 30):
            dist = 15 
        elif(percdelta > 30 and percdelta <= 50):
            dist = 20  
        elif(percdelta > 50 and percdelta <= 70):
            dist = 25  
        elif(percdelta > 70 and percdelta <= 90):
            dist = 30 
        else:
            dist = 35
        return dist

def draw_detections(img, rects, thickness = 1):
    for x, y, w, h in rects:
        # the HOG detector returns slightly larger rectangles than the real objects.
        # so we slightly shrink the rectangles to get a nicer output.
        pad_w, pad_h = int(0.15*w), int(0.05*h)
        cv2.rectangle(img, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)

if __name__ == '__main__':

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector( cv2.HOGDescriptor_getDefaultPeopleDetector() )
    cap=cv2.VideoCapture('videos/video1.mov')
    print('STARTING')
    while True:
        ret,frame=cap.read()
        height = frame.shape[0]
        if not ret: continue
        # frame = cv2.imread('images/ped0.jpeg')
        rects,w=hog.detectMultiScale(frame, winStride=(8,8), padding=(32,32), scale=1.05)

        #non-maximal suppression
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

        # draw the final bounding boxes
        for (xA, yA, xB, yB) in pick:
            cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 0, 255), 2)
            # distance = determine_distance(height, yA, yB)
            # text = '{}ft'.format(distance)
            text = 'Weight: xxx'
            # cv2.putText(frame, text, org=(xA,yA), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5, color=(255,0,0))
            cv2.putText(frame, text, org=(xA,yA), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                        fontScale=0.5, color=(255,0,0), thickness=2)
        # print('Found: {}'.format(len(rects)))
        # draw_detections(frame,rects)
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xff == ord('q'):
            break
    cv2.destroyAllWindows()