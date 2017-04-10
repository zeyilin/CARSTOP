#include "network.h"
#include "detection_layer.h"
#include "region_layer.h"
#include "cost_layer.h"
#include "utils.h"
#include "parser.h"
#include "box.h"
#include "image.h"
#include "demo.h"
#include <sys/time.h>

#define FRAMES 1

#ifdef OPENCV
#include "opencv2/highgui/highgui_c.h"
#include "opencv2/videoio/videoio_c.h"
#include "opencv2/imgproc/imgproc_c.h"

#include <stdio.h>
#include <sys/types.h> 
#include <sys/socket.h>
#include <netinet/in.h>

image get_image_from_stream(CvCapture *cap, int socketnum);

static char **demo_names;
static image **demo_alphabet;
static int demo_classes;

static float **probs;
static box *boxes;
static network net;
static image in   ;
static image in_s ;
static image det  ;
static image det_s;
static image disp = {0};
static CvCapture * cap;
//new ---
int sendFUSION = 1;
static int sendDSRC;
static int recvDSRC;
static int sendMMWV;
static int recvMMWV;
int sockfd = -1;
static int boxwidth = 8;
static char socketbuf[9];
static float dsrc_rgb[3];
static int delay;
// ---
static float fps = 0;
static float demo_thresh = 0;
static float demo_hier_thresh = .5;

static float *predictions[FRAMES];
static int demo_index = 0;
static image images[FRAMES];
static float *avg;

// --- stops communication but continues running YOLO
void *commStop(void *ptr)
{
	shutdown(sockfd,2);
	close(sockfd);
	sockfd = -1;
}
// ---

void *fetch_in_thread(void *ptr)
{
	// --- edit to gather images from mmwave-sent video when applicable
	if (recvMMWV){
		in = get_image_from_stream(cap, sockfd);
	} else {
		in = get_image_from_stream(cap, -1);
	}
	// ---
    if(!in.data){
        error("Stream closed.");
    }
    in_s = resize_image(in, net.w, net.h);
    return 0;
}

void *detect_in_thread(void *ptr)
{
    float nms = .4;

    layer l = net.layers[net.n-1];
    float *X = det_s.data;
    // --- added delay constraint
    if(delay == 0){
    // ---
    float *prediction = network_predict(net, X);

    memcpy(predictions[demo_index], prediction, l.outputs*sizeof(float));
    mean_arrays(predictions, FRAMES, l.outputs, avg);
    l.output = avg;

    free_image(det_s);
    if(l.type == DETECTION){
        get_detection_boxes(l, 1, 1, demo_thresh, probs, boxes, 0);
    } else if (l.type == REGION){
        get_region_boxes(l, 1, 1, demo_thresh, probs, boxes, 0, 0, demo_hier_thresh);
    } else {
        error("Last layer must produce detections\n");
    }
    if (nms > 0) do_nms(boxes, probs, l.w*l.h*l.n, l.classes, nms);
    printf("\033[2J");
    printf("\033[1;1H");
    printf("\nFPS:%.1f\n",fps);
    printf("Objects:\n\n");
    // --- added delay constraint
    }
    // ---

    images[demo_index] = det;
    det = images[(demo_index + FRAMES/2 + 1)%FRAMES];
    demo_index = (demo_index + 1)%FRAMES;
    
	// --- send info to DSRC
	if ((sockfd >= 0) && sendDSRC){
		box b;
		int loopcounter, class, left, right, top, bot, sendlen;
		unsigned char highbyte;
		float prob;
		for (loopcounter = 0; loopcounter < l.w*l.h*l.n; ++loopcounter){
			class = max_index(probs[loopcounter], demo_classes);
			prob = probs[loopcounter][class];
			if(prob > demo_thresh){
				bzero(socketbuf, 9);
				socketbuf[0] = (unsigned char) class;
				b = boxes[loopcounter];
				left  = (b.x-b.w/2.)*det.w;
				right = (b.x+b.w/2.)*det.w;
				top   = (b.y-b.h/2.)*det.h;
				bot   = (b.y+b.h/2.)*det.h;
				highbyte = left / 256;
				socketbuf[1] = highbyte;
				socketbuf[2] = (unsigned char) left - highbyte;
				highbyte = right / 256;
				socketbuf[3] = highbyte;
				socketbuf[4] = (unsigned char) right - highbyte;
				highbyte = top / 256;
				socketbuf[5] = highbyte;
				socketbuf[6] = (unsigned char) top - highbyte;
				highbyte = bot / 256;
				socketbuf[7] = highbyte;
				socketbuf[8] = (unsigned char) bot - highbyte;
				sendlen = write(sockfd, socketbuf, 9);
				if(sendlen < 9){
					printf("sending failed\n");
					commStop(0);
				}
			}
		}
		bzero(socketbuf, 9);
		socketbuf[0] = 'E';
		sendlen = write(sockfd, socketbuf, 9);
		if(sendlen < 9){
			printf("sending failed\n");
			commStop(0);
		}
	}
    if ((sockfd >= 0) && recvDSRC){
		bzero(socketbuf, 9);
        int rcvlen = read(sockfd, socketbuf, 9);
        if (rcvlen < 9){
            commStop(0);
        }
        char location = socketbuf[0];
        if (location == 'C'){
            int left = socketbuf[2];
            if (left < 0) left = left + 256; // signed to unsigned
            left = left + socketbuf[1]*256;
            int right = socketbuf[4];
            if (right < 0) right = right + 256;
            right = right + socketbuf[3]*256;
            int top = socketbuf[6];
            if (top < 0) top = top + 256;
            top = top + socketbuf[5]*256;
            int bot = socketbuf[8];
            if (bot < 0) bot = bot + 256;
            bot = bot + socketbuf[7]*256;
            draw_box_width(det, left, top, right, bot, boxwidth,
							dsrc_rgb[0], dsrc_rgb[1], dsrc_rgb[2]);
            image label = get_label(demo_alphabet, "DSRC", (720*.03)/10);
            draw_label(det, top + boxwidth, left, label, dsrc_rgb);
        } else if (location == 'N'){
            commStop(0);
        } else {
            draw_arrow(det, location, (char) socketbuf[1], dsrc_rgb[0], dsrc_rgb[1], dsrc_rgb[2]);
        }
    }
    // ---
    draw_detections(det, l.w*l.h*l.n, demo_thresh, boxes, probs, demo_names, demo_alphabet, demo_classes);
    return 0;
}

double get_wall_time()
{
    struct timeval time;
    if (gettimeofday(&time,NULL)){
        return 0;
    }
    return (double)time.tv_sec + (double)time.tv_usec * .000001;
}

void demo(char *cfgfile, char *weightfile, float thresh, int cam_index, const char *filename, char **names, int classes, int frame_skip, char *prefix, float hier_thresh)
{
    //skip = frame_skip;
    image **alphabet = load_alphabet();
    delay = frame_skip; // --- moved declaration
    demo_names = names;
    demo_alphabet = alphabet;
    demo_classes = classes;
    demo_thresh = thresh;
    demo_hier_thresh = hier_thresh;
    printf("Demo\n");
    net = parse_network_cfg(cfgfile);
    if(weightfile){
        load_weights(&net, weightfile);
    }
    set_batch_network(&net, 1);

    srand(2222222);

    // --- read options from democfg.txt
    FILE *cfgfileme = fopen("democfg.txt", "r");
    char foreignaddr[16];
    bzero(foreignaddr,16);
    int socketport;
    char vidname[20];
    bzero(vidname, 20);
    fscanf(cfgfileme, "%d %d %d %d %d %s %s", &sendDSRC, &recvDSRC, &sendMMWV,
                                 &recvMMWV, &socketport, foreignaddr, vidname);
    in_addr_t foreign_address = inet_addr(foreignaddr);
    fclose(cfgfileme);
    if (sendDSRC || recvDSRC || recvMMWV || sendFUSION) printf("receiving %d\n",socketport);
    // ---

    if(filename){
        printf("video file: %s\n", filename);
        cap = cvCaptureFromFile(filename);
    // --- don't use camera if you are receiving streamed video
    } else if (recvMMWV){
    // ---
    } else {
        cap = cvCaptureFromCAM(cam_index);
        cvSetCaptureProperty(cap, CV_CAP_PROP_FRAME_WIDTH, 1280);
        cvSetCaptureProperty(cap, CV_CAP_PROP_FRAME_HEIGHT, 720);
        cvSetCaptureProperty(cap, CV_CAP_PROP_FPS, 10);
        if(!cap) error("Couldn't connect to webcam.\n");
    }
    
    
    //--- set up sockets for DSRC
    struct sockaddr_in serv_addr;
	socklen_t addrlen = sizeof(serv_addr);
	bzero((char *) &serv_addr, addrlen);
	serv_addr.sin_family = AF_INET;
	serv_addr.sin_port = htons(socketport);
	dsrc_rgb[0] = 0.0;
    dsrc_rgb[1] = 0.1;
    dsrc_rgb[2] = 0.99;
	
	if (sendDSRC || recvDSRC || recvMMWV || sendFUSION){
	    int tempfd;
		struct sockaddr_in cli_addr;
		tempfd = socket(AF_INET, SOCK_STREAM, 0);
		if (tempfd < 0)
			error("ERROR opening socket\n");
		serv_addr.sin_addr.s_addr = INADDR_ANY;
		if (bind(tempfd, (struct sockaddr *) &serv_addr, addrlen) < 0)
			error("ERROR on binding\n");
		printf("waiting for connection...\n");
		listen(tempfd,5);
		int clilen = sizeof(cli_addr);
		sockfd = accept(tempfd, (struct sockaddr *) &cli_addr, &addrlen);
		if (sockfd < 0)
			error("ERROR on accept\n");
		printf("connected!\n");
	}
	if (sendMMWV){
		sockfd = socket(AF_INET, SOCK_STREAM, 0);
		if (sockfd < 0)
			error("ERROR opening socket\n");
		serv_addr.sin_addr.s_addr = foreign_address;
		printf("waiting for connection...\n");
		int connresult = connect(sockfd, (struct sockaddr *) &serv_addr, addrlen);
		if (connresult < 0)
			error("ERROR  connecting\n");
		printf("connected!\n");
	}
	// ---

    layer l = net.layers[net.n-1];
    int j;

    avg = (float *) calloc(l.outputs, sizeof(float));
    for(j = 0; j < FRAMES; ++j) predictions[j] = (float *) calloc(l.outputs, sizeof(float));
    for(j = 0; j < FRAMES; ++j) images[j] = make_image(1,1,3);

    boxes = (box *)calloc(l.w*l.h*l.n, sizeof(box));
    probs = (float **)calloc(l.w*l.h*l.n, sizeof(float *));
    for(j = 0; j < l.w*l.h*l.n; ++j) probs[j] = (float *)calloc(l.classes, sizeof(float));

    pthread_t fetch_thread;
    pthread_t detect_thread;

    fetch_in_thread(0);
    det = in;
    det_s = in_s;

    fetch_in_thread(0);
    detect_in_thread(0);
    disp = det;
    det = in;
    det_s = in_s;

    for(j = 0; j < FRAMES/2; ++j){
        fetch_in_thread(0);
        detect_in_thread(0);
        disp = det;
        det = in;
        det_s = in_s;
    }

    int count = 0;
    if(!prefix){
        cvNamedWindow(vidname, CV_WINDOW_NORMAL); 
        cvMoveWindow(vidname, 0, 0);
        cvResizeWindow(vidname, 1280, 720);
    }

    double before = get_wall_time();

    while(1){
        ++count;
        if(1){
            if(pthread_create(&fetch_thread, 0, fetch_in_thread, 0)) error("Thread creation failed");
            if(pthread_create(&detect_thread, 0, detect_in_thread, 0)) error("Thread creation failed");

            if(!prefix){
            	// --- send entire image via mmwave
                if ((sockfd >= 0) && (sendMMWV)){
	                int w = 1280;
	                int h = 720;
	                int c = 3;
	                int cstep = w*h;
	                int i;
	                int msgLen = cstep * c;
	                int escapeCount = 1000000;
	                int msgsent = 0;
	                int sentlen, tosend;
	                unsigned char buffer[4097];
	                char ack[3];
	                while((escapeCount > 0) && (msgsent < msgLen)){
		                bzero(buffer, 4097);
		                if (msgLen - msgsent < 4096){
			                tosend = msgLen - msgsent;
		                } else {
			                tosend = 4096;
		                }
		                for(i=0; i<tosend; ++i){
			                buffer[i] = disp.data[msgsent + i]*255;
		                }
		                sentlen = write(sockfd, buffer, tosend);
		                if (sentlen < 0){
			                printf("sending mmwave broke\n");
			                commStop(0);
			                break;
		                }
		                escapeCount--;
		                msgsent = msgsent + sentlen;
	                }
	                bzero(ack, 3);
	                sentlen = read(sockfd, ack, 3);
	                if (sentlen < 3){
		                printf("Err on ack\n");
		                commStop(0);
	                }
                } else {
                // ---
                show_image(disp, vidname);
                int c = cvWaitKey(1);
                if (c == 10){
                    if(frame_skip == 0) frame_skip = 60;
                    else if(frame_skip == 4) frame_skip = 0;
                    else if(frame_skip == 60) frame_skip = 4;   
                    else frame_skip = 0;
                }
                // --- send entire image via mmwave
                }
                // ---
            }else{
                char buff[256];
                sprintf(buff, "%s_%08d", prefix, count);
                save_image(disp, buff);
            }

            pthread_join(fetch_thread, 0);
			pthread_join(detect_thread, 0);
			
            if(1){//(delay == 0){
                free_image(disp);
                disp  = det;
            }
            det   = in;
            det_s = in_s;
        }else {
            fetch_in_thread(0);
            det   = in;
            det_s = in_s;
            detect_in_thread(0);
            if(delay == 0) {
                free_image(disp);
                disp = det;
            }
            show_image(disp, "Demo");
            cvWaitKey(1);
        }
        --delay;
        if(delay < 0){
            delay = frame_skip;

            double after = get_wall_time();
            float curr = 1./(after - before);
            fps = curr;
            before = after;
        }
    }
}
#else
void demo(char *cfgfile, char *weightfile, float thresh, int cam_index, const char *filename, char **names, int classes, int frame_skip, char *prefix, float hier_thresh)
{
    fprintf(stderr, "Demo needs OpenCV for webcam images.\n");
}
#endif

