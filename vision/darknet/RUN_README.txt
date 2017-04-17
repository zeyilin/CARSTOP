
*** Run using webcam ***
./darknet detector demo cfg/coco.data cfg/yolo.cfg yolo.weights -c 1

*** Run using video ***
./darknet detector demo cfg/coco.data cfg/yolo.cfg yolo.weights /path/to/video

*** Run using photo ***
./darknet detector test cfg/coco.data cfg/yolo.cfg yolo.weights /path/to/photo
