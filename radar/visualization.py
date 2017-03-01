import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from math import pi

data = np.genfromtxt('C:\Users\Steven\Documents\Senior Year\Senior Design\CARSTOP2\\radar\RADAR_FEB26_DATA\\radar_preGFM_B2.txt', delimiter=',', names=True, usecols = (0, 1, 2, 3, 6))
pandata = pd.DataFrame(data, columns=['time', 'track', 'range', 'angle', 'power'])
index = 0
stride_size = .1
cur_stride = 1
r = data['range']
theta = data['angle'] * pi/ 180 + pi/2
area = data['power'] * 5
colors = data['track']
x = r * np.cos(theta)
y = r * np.sin(theta)
plt.ion()
plt.subplot(111)

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
        x = -r * np.cos(theta)
        y = r * np.sin(theta)
        plt.title("Current Time %f." % (stride_size * cur_stride))
        plt.axis([-50, 50, 0, 50])
        scatted = plt.scatter(x, y, area, colors)
        plt.draw()
    plt.pause(.005)
    plt.cla()
    cur_stride += 1