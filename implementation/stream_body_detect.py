import numpy as np
import cv2
from imutils.object_detection import non_max_suppression

def draw_detections(img, rects, thickness = 1):
    for x, y, w, h in rects:
        # the HOG detector returns slightly larger rectangles than the real objects.
        # so we slightly shrink the rectangles to get a nicer output.
        pad_w, pad_h = int(0.15*w), int(0.05*h)
        cv2.rectangle(img, (x+pad_w, y+pad_h), (x+w-pad_w, y+h-pad_h), (0, 255, 0), thickness)


if __name__ == '__main__':

    hog = cv2.HOGDescriptor()
    hog.setSVMDetector( cv2.HOGDescriptor_getDefaultPeopleDetector() )
    cap=cv2.VideoCapture(0)
    while True:
        ret,frame=cap.read()
        if not ret: continue
        # frame = cv2.imread('images/ped0.jpeg')
        rects,w=hog.detectMultiScale(frame, winStride=(8,8), padding=(32,32), scale=1.05)

        #non-maximal suppression
        rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
        pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

        # draw the final bounding boxes
        for (xA, yA, xB, yB) in pick:
            cv2.rectangle(frame, (xA, yA), (xB, yB), (0, 0, 255), 2)

        print('Found: {}'.format(len(rects)))
        draw_detections(frame,rects)
        cv2.imshow('Video', frame)
        if cv2.waitKey(1) & 0xff == ord('q'):
            break
    cv2.destroyAllWindows()