# import the necessary packages
from __future__ import print_function
from imutils.object_detection import non_max_suppression
from imutils import paths
import numpy as np
import argparse
import imutils
import cv2
import time

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
    image_height = image.shape[0]
    image_width = image.shape[1]

    # image = imutils.resize(image, width=min(400, image.shape[1]))
    orig = image.copy()

    # detect people in the image
    (rects, weights) = hog.detectMultiScale(image, winStride=(4, 4), padding=(32, 32), scale=1.05)

    # draw the original bounding boxes
    for (x, y, w, h) in rects:
        cv2.rectangle(orig, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # apply non-maxima suppression to the bounding boxes using a
    # fairly large overlap threshold to try to maintain overlapping
    # boxes that are still people
    rects = np.array([[x, y, x + w, y + h] for (x, y, w, h) in rects])
    suppressed_rects = non_max_suppression(rects, probs=None, overlapThresh=0.65)

    for (x0, y0, x1, y1) in suppressed_rects:
        cv2.rectangle(image, (x0, y0), (x1, y1), (0, 255, 0), 2)
        dist = determine_distance(image_height, y1)
        text = '{}ft'.format(dist)
        cv2.putText(image, text, org=(x0,y0), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                        fontScale=0.5, color=(255,0,0), thickness=2)
        object_x = (x0+x1)/2
        alert = side_alert(image_width, object_x)
        if alert:
            cv2.putText(image, alert, org=(x0,y0+15), fontFace=cv2.FONT_HERSHEY_DUPLEX,
                        fontScale=0.5, color=(0,0,255), thickness=2)

    print("Detection... {:.3f}s".format(time.time()-start))

    # show some information on the number of bounding boxes
    filename = imagePath[imagePath.rfind("/") + 1:]
    print("[INFO] {}: {} original boxes, {} after suppression".format(
        filename, len(rects), len(suppressed_rects)))

    # show the output images
    cv2.imshow("Before NMS", orig)
    cv2.imshow("After NMS", image)
    cv2.waitKey(0)