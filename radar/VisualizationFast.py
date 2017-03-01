import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import pandas as pd
from math import pi


#reading data for the graphing into a data element
data = np.genfromtxt('C:\Users\Steven\Documents\Senior Year\Senior Design\CARSTOP2\\radar\RADAR_FEB26_DATA\\radar_preGFM_B2.txt', delimiter=',', names=True, usecols = (0, 1, 2, 3, 6))
pandata = pd.DataFrame(data, columns=['time', 'track', 'range', 'angle', 'power'])
index = 0
stride_size = .1

#initializing our figure
fig = plt.figure()
ax = plt.axes(xlim=(-50, 50), ylim=(0, 80))
time_text = ax.text(0.05, 0.95,'',horizontalalignment='left',verticalalignment='top', transform=ax.transAxes)
pathcol = plt.scatter([], [], s=100)


def init():
    pathcol.set_offsets([[], []])
    #time_text.set_text('hello')
    return [pathcol]

def update(i, pathcol):
    global index
    start_index = index
    while pandata.iloc[index][0] < stride_size*i:
        index += 1
    data_slice = pandata[start_index:index]
    if index != start_index:
        r = data_slice['range']
        theta = data_slice['angle'] * pi/ 180 + pi/2
        area = data_slice['power'] * 5
        colors = data_slice['track']
        x = -r * np.cos(theta)
        y = r * np.sin(theta)
        pathcol.set_offsets(np.vstack((x, y)).T)
        plt.title("Current Time %f." % (stride_size * i))
        #pathcol.set_color(colors)
        pathcol.set_sizes(area)
    time_text.set_text('time = %.1f' % (i * stride_size))  # <<<<<Here. This doesn't work
    return [pathcol] + [time_text]

anim = animation.FuncAnimation(
    fig, update, init_func=init, fargs=(pathcol,), interval= (10*stride_size),
    blit=True, repeat=True)
plt.show()