import numpy as np
#from pylab import *
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi
data = np.genfromtxt('C:\\Users\\adees\\Google Drive\\Classes\\_Senior Design\\Raw Data\\CARSTOP_TEST_FEB26\\RADAR & DSRC\\radar_preGFM_B3.txt', delimiter=',', names=True, usecols = (0, 1, 2, 3, 6))
pandata = pd.DataFrame(data, columns=['time', 'track', 'range', 'angle', 'power'])
index = 0
stride_size = .1
cur_stride = 1
plt.ion()


while 1:
    start_index = index
    while pandata.iloc[index][0] < stride_size*cur_stride:
        index += 1
    data_slice = pandata[start_index:index]
    if index != start_index:
        r = data_slice['range']
        theta = data_slice['angle'] * pi/ 180 + pi/2
        area = data_slice['power'] * 5
        colors = data_slice['track']
        plt.subplot(111, projection='polar')
        plt.scatter(theta, r, area, colors)
        plt.title("Current Time %f." % (stride_size * cur_stride))
        plt.axis([pi/4, 3 * pi / 4, 0, 50])
    plt.pause(0.0001)
    plt.clf()
    cur_stride += 1