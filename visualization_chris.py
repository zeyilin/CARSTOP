import numpy as np
import pandas as pd
from math import pi
import sys, os
import random
import time
from matplotlib import pyplot as plt
from matplotlib import animation
from sklearn.cluster import DBSCAN


filePath = 'radar_preGFM_C2.txt'
#reading data for the graphing into a data element
data = np.genfromtxt(filePath, delimiter=',', names=True, usecols = (0, 1, 2, 3, 6))

pandata = pd.DataFrame(data, columns=['time', 'track', 'range', 'angle', 'power'])
delay = .3
class RegrMagic(object):
    """Mock for function Regr_magic()
    """
    def __init__(self, data):
        self.data = data
    def __call__(self,data):
#         time.sleep(.1)
        toRet = self.data[(self.data['time']>time.time()-startTime-delay)&(self.data['time']<time.time()-startTime)]
#         filtered = DBSCAN.fit_predict(toRet)
        return toRet

nextFrame = RegrMagic(pandata)

def frames():
    while True:
        yield nextFrame(pandata)

fig = plt.figure()
ax = plt.axes(xlim=(-10, 10), ylim=(0, 40))
plt.axvline(x=0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r')
plt.axvline(x=-0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r') 

plt.axvline(x=-1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')
plt.axvline(x=1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')

plt.axvline(x=-5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')
plt.axvline(x=5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')
scatter = plt.scatter([], [])
startTime = time.time()
def animate(data_slice, scatter):
    print(data_slice)
    r = data_slice['range']
    theta = data_slice['angle'] * pi/ 180 + pi/2
    area = data_slice['power'] * 5
    colors = data_slice['track']
    x = -r * np.cos(theta)
    y = r * np.sin(theta)
#     toCluster = pd.DataFrame()
#     toCluster['x'] = x
#     toCluster['y'] = y
    scatter.set_offsets(np.vstack((x,y)).T)
    scatter.set_sizes(area)
#     scatter.set_color(colors)
    plt.title("Current Time %f." % (time.time()-startTime))
    return scatter


anim = animation.FuncAnimation(fig, animate,frames=frames, fargs=[scatter], interval=33, blit=True)
plt.show()