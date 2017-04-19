# -*- coding: utf-8 -*-
"""
last mod 12/17/16
GFM = grouping, filtering, and merging tracked objects
The standard Delphi radar performs all of these, but we have the raw-data version
The exact way that this is performed is mostly made up at the moment, and will
probably undergo a lot of change
"""

import pandas as pd
import numpy as np

## returns the distance in meters between two range,angle points
def polarDist(r1,r2,o1,o2): return (r1**2.+r2**2.-2*r1*r2*np.cos(o1-o2))**.5
## returns the width the nearer object would have to be to block the view of the farther object
def lateralDist(r1,r2,o1,o2): return np.minimum(r1,r2)*np.tan(np.abs(o1-o2))
##
def polarMean(r,o):
    x, y = np.mean(r*np.cos(o)), np.mean(r*np.sin(o))
    return ( (x**2.+y**2.)**.5 , np.arctan2(y,x) )

## takes a similarity matrix (symmetric boolean matrix) and returns 
## blocks connected by true values
def blockFinder(matrix):
    remaining = set(range(matrix.shape[0]))
    counter = 0
    blocks = []
    while len(remaining) > 0 and counter < 1000:
        element = remaining.pop()
        blocks += [_blockAlgoRecurse(matrix, remaining, element,0)]
        counter += 1
    assert counter < 1000, "infinite while"
    return blocks
def _blockAlgoRecurse(matrix, remaining, i, counter):
    #remaining = set(range(matrix.shape[0]))
    group = [i]
    counter += 1
    assert counter < 1000, 'infinite recurse'
    for j in range(matrix.shape[0]):
        if j in remaining and matrix[i,j]:
            remaining.remove(j)
            group += _blockAlgoRecurse(matrix,remaining,j, counter)
    return group

output_period = 0.2 #s
group_maxDist = 7.0 #m
group_maxTime = 0.3 #s
filter_Time = 0.1 #s
filter_minPower = 10 #
merge_minDist = 2. #m , objects this close to eachother are merged
    
## merging
# obj[0] = time, obj[1] = range, obj[2] = angle
# values can be constants or nd-arrays
# returns True if the objects should be merged
def locateMerge_mean(obj1, obj2):
    return polarDist(obj1[1], obj2[1], obj1[2], obj2[2]) < merge_minDist
    
def locateMerge_closest(obj1, obj2):
    return lateralDist(obj1[1], obj2[1], obj1[2], obj2[2]) < merge_minDist
    
def makeMerge_mean(objs):
    time = np.max(objs[:,0])
    rangex, angle = polarMean(objs[:,1], objs[:,2])
    return (time,rangex,angle)
    
def makeMerge_closest(objs):
    return objs[np.argmin(objs[:,1])]

class RadarGFM():
    def __init__(self):
        track_columns = ['first','last','power','range','angle']
        self.tracks = pd.DataFrame(np.zeros((64,len(track_columns)))-
                                   group_maxTime, columns=track_columns)

    def update(self, message):
        time,t,rangex,angle,rrate,lrate,power = message
        t = int(t)-1
        first,last,oldpower,oldrange,oldangle = self.tracks.iloc[t]
        ## grouping
        track_change = polarDist(rangex, oldrange, angle, oldangle)
        newTrack = track_change > group_maxDist or time > last + group_maxTime
        if newTrack:
            self.tracks.iloc[t,:] = [time, time, power, rangex, angle]
        elif time < last + filter_Time:
            self.tracks.iloc[t,:] = [first, time, power, rangex, angle]
            # for now, really dumb filtering
            rangex = (oldrange + rangex) / 2.
            angle = (angle + oldangle) / 2.
        else:
            self.tracks.iloc[t,:] = [first, time, power, rangex, angle]
            
    def output(self, time):
        filtered_tracks = (self.tracks['power'] > filter_minPower) &\
                  (self.tracks['last'] - self.tracks['first'] > filter_Time) &\
                  (time - self.tracks['last'] < output_period)
        output = self.tracks.loc[filtered_tracks, ['last','range','angle']]
        #output = output.rename({'last':'time'})
        output = output.values
        
        # first time, take the mean of tracks that are very close
        if output.shape[0] == 0: return output
        outputPairs = np.tile(output,(output.shape[0],1,1)).transpose(2,0,1)
        merge_matrix = locateMerge_mean(outputPairs,outputPairs.transpose(0,2,1))
        mergeblocks = blockFinder(merge_matrix)
        output = np.array([makeMerge_mean(output[block]) for block in mergeblocks])
        if output.shape[0] == 0: return output
        outputPairs = np.tile(output,(output.shape[0],1,1)).transpose(2,0,1)
        merge_matrix = locateMerge_closest(outputPairs,outputPairs.transpose(0,2,1))
        mergeblocks = blockFinder(merge_matrix)
        output = np.array([makeMerge_closest(output[block]) for block in mergeblocks])
        
        return output