from test_radar import Radar
from LIDAR import Lidar 
import sys, os, time
from DSRC import DsrcLog
from subprocess import call as terminalCall



""" stores the starting time, ending time, and ending status for any test """
class BasicLog():
    def __init__(self, filename):
        self.fil = open(filename, 'w+')
    def __enter__(self):
        return self
    def start(self, stime):
        timestring = '{}, {:.0f}'.format(time.ctime(int(stime)), stime%1*1000)+' ms'
        self.fil.write("start = "+timestring)
    def __exit__(self, errtype, errval, traceback):
        stime = time.time()
        timestring = '{}, {:.0f}'.format(time.ctime(int(stime)), stime%1*1000)+' ms'
        self.fil.write('\n end = '+timestring)
        if errtype == KeyboardInterrupt:
            self.fil.write('\n natural exit')
        else:
            self.fil.write(str(traceback))
            print errval
        self.fil.close()
        
if __name__ == '__main__':

    folder = "."
    if len(sys.argv) > 1:
        folder = sys.argv[1]

    if folder != "." and not os.path.isdir(folder):
        terminalCall(['mkdir',os.path.realpath(folder)], shell = os.name!='posix')

    radarFilename = folder + "/radar.csv"
    lidarFilename = folder + "/lidar.dat"
    dsrcFilename = folder + "/dsrc.txt"
    basicFilename = folder + "/basiclog.txt"

    with Radar(radarFilename) as radar,\
         BasicLog(basicFilename) as basiclog:
        print("All sensors initialized")
        
        startingtime = time.time()
        radar.start(startingtime)
        # lidar.start(startingtime)
        # dsrc.start(startingtime)
        basiclog.start(startingtime)
        print("All sensors logging")
        
        # option 1, let sensors run on their own even if others break down
        #time.sleep(30000)
        
        # option 2, check if any sensors stops and stop all sensors
        while True:
            time.sleep(1)
            assert radar.is_alive()
            # assert lidar.is_alive()
            # assert dsrc.is_alive()



         #Lidar('129.116.100.217', lidarFilename, waitOnStart=False) as lidar,\
         #DsrcLog(9001, dsrcFilename, waitOnStart=False) as dsrc,\
