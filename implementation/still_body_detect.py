# import the necessary packages
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
import time

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

# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-i", "--images", required=True, help="path to images directory")
args = vars(ap.parse_args())

# initialize the HOG descriptor/person detector
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# loop over the image paths
for imagePath in paths.list_images(args["images"]):
    # load the image and resize it to (1) reduce detection time
    # and (2) improve detection accuracy
    image = cv2.imread(imagePath)
    start = time.time()

    image = imutils.resize(image, width=min(400, image.shape[1]))
    height = image.shape[0]
    orig = image.copy()

    # detect people in the image
    (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4), padding=(32, 32), scale=1.05)

    print(weights)

    # draw the original bounding boxes
    for (x, y, w, h) in rects:
        cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # apply non-maxima suppression to the bounding boxes using a
    # fairly large overlap threshold to try to maintain overlapping
    # boxes that are still people
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    pick = non_max_suppression(rects, probs=None, overlapThresh=0.65)

    # draw the final bounding boxes
    for (xA, yA, xB, yB) in pick:
        cv2.rectangle(image, (xA, yA), (xB, yB), (0, 255, 0), 2)
        # distance = determine_distance(height, yA, yB)
        # text = '{}ft'.format(distance)
        text = 'Weight: xx' 
        cv2.putText(image, text, org=(xA,yA), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                    fontScale=0.5, color=(255,0,0), thickness=2)

    print("Detection... {:.3f}s".format(time.time()-start))

    # show some information on the number of bounding boxes
    filename = imagePath[imagePath.rfind("/") + 1:]
    print("[INFO] {}: {} original boxes, {} after suppression".format(
        filename, len(rects), len(pick)))

    # show the output images
    cv2.imshow("Before NMS", orig)
    cv2.imshow("After NMS", image)
    cv2.waitKey(0)