*** Make sure the democfg.txt is configured accordingly ***
<int sendDSRC> <int recbDSRC> <int sendMMWV> <int recvMMWV> <int socketport> <string foreignipaddr> <string videoname>
0 0 0 1 9002 127.0.0.1 Front_View


*** Run using webcam ***
./darknet detector demo cfg/coco.data cfg/yolo.cfg yolo.weights -c 1

*** Run using video ***
./darknet detector demo cfg/coco.data cfg/yolo.cfg yolo.weights /path/to/video

*** Run using photo ***
./darknet detector test cfg/coco.data cfg/yolo.cfg yolo.weights /path/to/photo
