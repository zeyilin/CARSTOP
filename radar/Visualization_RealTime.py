import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from math import pi
import matplotlib
from multiprocessing import Queue
import sys, os


time_text = ''
index = 0
stride_size = .1
pathcol = ''
def pipeline_radar(radarQueue):
    print "HERE I AM"
    #initializing our figure
    fig = plt.figure()
    ax = plt.axes(xlim=(-10, 10), ylim=(0, 20))
    global pathcol
    pathcol = plt.scatter([], [], s=100)
    global time_text
    time_text = ax.text(0.05, 0.95,'',horizontalalignment='left',verticalalignment='top', transform=ax.transAxes)
    # animating our variable
    anim = animation.FuncAnimation(fig, update, init_func=init, fargs=(pathcol,radarQueue), interval=(1000 * stride_size),blit=True, repeat=True)
    print "I MADE THE ANIMATION FUNCTION"
    #plt.ion()
    print "THE BACKEND IS" + plt.get_backend()
    plt.show()
    print "I shouldn't print here, plt.show() should not return"

#initializing our figure
#fig = plt.figure()
#ax = plt.axes(xlim=(-10, 10), ylim=(0, 25))
#plt.axvline(x=0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r')
#plt.axvline(x=-0.96266, linestyle = 'dotted', ymax = 0.5, color = 'r')

#plt.axvline(x=-1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')
#plt.axvline(x=1.8288, linestyle = 'dashed', ymax = 0.5, color = 'y')

#plt.axvline(x=-5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')
#plt.axvline(x=5.4864, linestyle = 'dashed', ymax = 0.5, color = 'y')

#time_text = ax.text(0.05, 0.95,'',horizontalalignment='left',verticalalignment='top', transform=ax.transAxes)
#pathcol = plt.scatter([], [], s=100)


def init():
    global pathcol
    pathcol.set_offsets([[], []])
    #time_text.set_text('hello')
    return [pathcol]

def update(i, pathcol, radarQueue ):
    columns = ['time', 'track', 'range', 'angle', 'something', 'garbage', 'power']
    index = 0
    r = []
    theta =  []
    area = []
    x = []
    y = []
    while not radarQueue.empty():
        radarmessage = radarQueue.get()
        for entry in radarmessage:
            print entry
            r.append(entry[2])
            theta.append(entry[3] * pi/ 180 + pi/2)
            area.append(entry[6] * 5)
            x.append(-r[index] * np.cos(theta[index]))
            y.append(r[index] * np.sin(theta[index]))
            index = index + 1
    print "X offsets to be printed: " + str(x)
    print "Y offsets to be printed" + str(y)
    print "Sizes of the objects" + str(area)
    pathcol.set_offsets(np.vstack((x, y)).T)
    plt.title("Current Time %f." % (stride_size * i))
    pathcol.set_sizes(area)
    global time_text
    time_text.set_text('time = %.1f' % (i * stride_size))
    return [pathcol] + [time_text]