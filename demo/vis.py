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


delay = .3
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
            # logfile.write('time,track,range,angle,rangerate,latrate,power')
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
    print pandata
    nextFrame = RegrMagic(pandata)
    startTime = time.time()
    boxes = []
    anim = animation.FuncAnimation(fig, animate, frames=frames, fargs=[scatter,ax,boxes], interval=50, blit=False)
    plt.show()


def frames():
    while True:
        yield nextFrame(pandata)

def animate(data_slice, scatter,ax,boxes):
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
        filtered = DBSCAN(eps=3.0,min_samples=4).fit_predict(temp)
    else:
        filtered= []
    temp['filter'] = filtered
    toPrint = pd.DataFrame(columns=['x','y', 'minx', 'miny', 'width', 'height', 'angle'])
    for group in pd.Series(filtered).unique():
        if group>-1:
            subset = temp[temp['filter']==group]
            linReg = LinearRegression().fit(subset['x'].reshape(-1,1),subset['y'])
            rotAngle = np.rad2deg(np.arctan2(linReg.coef_[0],1))
            rotation_matrix = pd.DataFrame(columns=['a','b'])
            rotation_matrix.loc[0] = (math.cos(-math.radians(rotAngle)), -math.sin(-math.radians(rotAngle)))
            rotation_matrix.loc[1] = (math.sin(-math.radians(rotAngle)), math.cos(-math.radians(rotAngle)))
            
            rotatedSubset = np.matmul(subset[['x','y']].as_matrix(),rotation_matrix.as_matrix())
            rotatedSubset = pd.DataFrame(rotatedSubset, columns=['x','y'])
            minSubx = rotatedSubset['x'].min()
            minSuby = rotatedSubset['y'].min()
            toPrint.loc[group] = (subset['x'].mean(), subset['y'].mean(), 
                                  minSubx, minSuby, 
                                  rotatedSubset['x'].max()-minSubx, 
                                  rotatedSubset['y'].max()-minSuby,
                                  rotAngle)
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
    # scatter.set_offsets(np.vstack((temp['x'],temp['y'])).T)
    if len(toPrint)>0:
        scatter.set_offsets(np.vstack((toPrint['x'],toPrint['y'])).T)
        scatter.set_sizes(area)
    scatter.set_color(colors)
    plt.title("Current Time %f." % (time.time()-startTime))
    radarBoxes.put(toPrint)
    return scatter

