import VisualizationFast as VFas
import numpy as np
import pandas as pd
from multiprocessing import Process, Queue
from time import sleep

if __name__ == '__main__':
    data = np.genfromtxt(
        'C:\Users\Steven\Documents\Senior Year\Senior Design\CARSTOP2\\radar\RADAR_FEB26_DATA\\radar_preGFM_B2.txt',
        delimiter=',', names=True, usecols=(0, 1, 2, 3, 6))
    pandata = pd.DataFrame(data, columns=['time', 'track', 'range', 'angle', 'power'])
    radarQueue = Queue()
    p = Process(target=VFas.pipeline_radar, args=(radarQueue,))
    p.start()
    index = 1;
    stride_size = .01
    time = 0;
    start_index = 1;
    while(True & index < pandata.size):
        while (index < pandata.size) & (pandata.iloc[index][0] < time):
            index += 1
        print pandata.iloc[start_index:index]
        radarQueue.put(pandata.iloc[start_index:index])
        start_index = index;
        sleep(stride_size)
        time = time + stride_size
    p.join()
