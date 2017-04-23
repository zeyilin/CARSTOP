import numpy as np
import pandas as pd
from math import pi
import sys, os
import random
import time
from matplotlib import pyplot as plt
from matplotlib import animation
from sklearn.cluster import DBSCAN
from matplotlib import patches
from sklearn.linear_model import LinearRegression
import math
from matplotlib import transforms


delay = .2
offset = 0
startTime = 0
boxes = []
nextFrame = None
pandata = pd.DataFrame(columns=['time', 'track', 'range', 'angle', 'trash', 'more trash', 'power'])
data = None # this is a queue
fileName = None
radarBoxes = None

# converts a 2D array to a csv string
def array2str(array):
    return '\n'.join((','.join((str(ele) for ele in row)) for row in array))

class RegrMagic(object):
    """Mock for function Regr_magic()
    """
    def __init__(self, data):
        self.data = data
    def __call__(self,_data):
#         time.sleep(.1)
        global delay, offset, pandata, data
        with open(fileName, 'a') as logfile:
            logfile.write('time,track,range,angle,rangerate,latrate,power')
            while not data.empty():
                msgs = data.get()
                temp = pd.DataFrame(msgs, columns=['time', 'track', 'range', 'angle', 'trash', 'more trash', 'power'],)
                logfile.write('\n' + array2str(msgs))
                pandata = pd.concat([pandata, temp])
            pandata = pandata[pandata['time'] > (time.time() - delay)]
            pandata = pandata[pandata['range'] < 50.0]
        return pandata


def pipeline_radar(radarData, filename, rbox):
    #initializing our figure
    fig = plt.figure()
    ax = plt.axes(xlim=(-10, 10), ylim=(0, 40))
    plt.axvline(x=0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r')
    plt.axvline(x=-0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r') 

    plt.axvline(x=-1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')
    plt.axvline(x=1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')

    plt.axvline(x=-5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')
    plt.axvline(x=5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')
    scatter = plt.scatter([], [])
    global boxes, nextFrame, startTime, nextFrame, pandata, data, fileName, radarBoxes
    radarBoxes = rbox
    fileName = filename
    pandata = pd.DataFrame(columns=['time', 'track', 'range', 'angle', 'power'])
    data = radarData
    msgs = data.get()
    for msg in msgs:
        pandata = pandata.append({ 'time'  : msg[0],
                                     'track' : msg[1],
                                     'range' : msg[2],
                                     'angle' : msg[3],
                                     'power' : msg[6]}, ignore_index = True)
    # print pandata
    nextFrame = RegrMagic(pandata)
    startTime = time.time()
    boxes = []
    anim = animation.FuncAnimation(fig, animate, frames=frames, fargs=[scatter,ax,boxes], interval=50, blit=False)
    plt.show()


def frames():
    while True:
        yield nextFrame(pandata)

def animate(data_slice, scatter,ax,boxes):
    start = time.time()
    # print(data_slice)
    global startTime, pandata, data, radarBoxes
    # print pandata.shape
    r = data_slice['range']
    theta = data_slice['angle'] * pi/ 180 + pi/2
    area = data_slice['power'] * 5
    colors = data_slice['track']
    x = -r * np.cos(theta)
    y = r * np.sin(theta)
    temp = pd.DataFrame()
    temp['x'] = x
    temp['y'] = y
    if len(temp)>0:
        filtered = DBSCAN(eps=1.5,min_samples=3).fit_predict(temp)
    else:
        filtered= []
    temp['filter'] = filtered
    toPrint = pd.DataFrame(columns=['x','y', 'minx', 'miny', 'width', 'height', 'angle', 'cluster_size', 'left_pixel', 'right_pixel'])
    # print('dbscan: ' + str(time.time()-start))
    # start = time.time()
    for group in pd.Series(filtered).unique():
        if group>-1:
            subset = temp[temp['filter']==group]
            linReg = LinearRegression().fit(subset['x'].values.reshape(-1,1),subset['y'])
            rotAngle = np.rad2deg(np.arctan2(linReg.coef_[0],1))
            
            cos = math.cos(-math.radians(rotAngle))
            sin = math.sin(-math.radians(rotAngle))
            rotation_matrix = np.matrix([(cos, -sin),(sin, cos)])
            # rotation_matrix.loc[0] = (cos, -sin)
            # rotation_matrix.loc[1] = (sin, cos)
            
            rotatedSubset = np.matmul(subset[['x','y']].as_matrix(),rotation_matrix)
            # rotatedSubset = pd.DataFrame(rotatedSubset, columns=['x','y'])

            minSubx, minSuby = np.amin(rotatedSubset, axis=0).tolist()[0]
            maxSubx, maxSuby = np.amax(rotatedSubset, axis=0).tolist()[0]
            width = maxSubx-minSubx
            height = maxSuby-minSuby
            alpha = [minSubx, minSuby + height]
            beta = [minSubx + width, minSuby]
            angle_points = np.matrix([alpha, beta])
            anti_rotation_matrix = pd.DataFrame(columns=['a','b'])
            anti_rotation_matrix.loc[0] = (cos, sin)
            anti_rotation_matrix.loc[1] = (-sin, cos)
            angle_points = np.matmul(angle_points, anti_rotation_matrix.as_matrix())
            left_angle = np.arctan2(angle_points[0,0],angle_points[0,1])
            right_angle = np.arctan2(angle_points[1,0],angle_points[1,1])
            radius = 640.0/np.cos(np.radians(51))
            left_pixel = np.sin(left_angle)*radius + 640
            right_pixel = np.sin(right_angle)*radius + 640
            toPrint.loc[group] = (subset['x'].mean(), subset['y'].mean(), 
                                  minSubx, minSuby, width, height, rotAngle, 
                                  len(subset),int(left_pixel), int(right_pixel))
    # print('rotation: ' + str(time.time()-start))
    # start = time.time()
    toRemove = []
    for box in boxes:
        try:
            box.remove()
        except ValueError:
            toRemove.append(box)
    for elem in toRemove:
        boxes.remove(elem)
    for piece in toPrint.iterrows():
        row = piece[1]
        box = patches.Rectangle( (row['minx'], row['miny']), row['width'], row['height'], fill=False)
        t = transforms.Affine2D().rotate_deg_around(0,0,-row['angle']) +  ax.transData 
        box.set_transform(t)
        boxes.append(box)
        ax.add_patch(box)
    # print('box removal: ' + str(time.time()-start))
    # start= time.time()
    scatter.set_offsets(np.vstack((temp['x'],temp['y'])).T)
    if len(toPrint)>0:
        comboPrint = pd.DataFrame(columns=['x','y', 'color', 'area'])
        toPrint['area'] = 3 * toPrint['cluster_size']
        toPrint['color'] = ['r' for i in range(len(toPrint))]
        temp['color'] = ['b' for i in range(len(temp))]
        temp['area'] = area
        comboPrint = pd.concat([temp[['x','y', 'color', 'area']], toPrint[['x','y', 'color', 'area']]])
        # for index, row in toPrint.iterrows():
        #     comboPrint.loc[index] = [row['x'], row['y'], 'r', row['cluster_size']*3]
        # for index, row in temp.iterrows():
        #     comboPrint.loc[len(toPrint)+index] = [row['x'], row['y'], 'b', 6]
        # print("Setting the offsets")
        # print(len(comboPrint))
        scatter.set_offsets(np.vstack((comboPrint['x'],comboPrint['y'])).T)
        scatter.set_sizes(comboPrint['area'])
        scatter.set_color(comboPrint['color'])
    # print("end: " + str(time.time()-start))
    plt.title("Current Time %f." % (time.time()-startTime))
    radarBoxes.put(toPrint)
    return scatter

