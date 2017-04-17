#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
last mod 4/7/17
writes LIDAR to file
"""

import socket, select, time, struct
from multiprocessing import Process
import numpy as np

## things that can be calculated in advance to speed things up
preamble = ''.join((chr(int(byte, 16)) for byte in ['75','bd','7e','97']))
preamble += struct.pack(">L", 6632)
firingidxlist = [firing*132 for firing in range(50)]
packedstructure = ">H"+"L"*8+"B"*8

angle_conversion = np.pi / 5200.
distance_conversion = 10.**-5
vertical_angles = [-.318505,-.2692,-.218009,-.165195,-.111003,-.0557982,0.,.0557982]


""" an internal method to read the Lidar packets and store the useful parts """
def _readFromLidar(msg, readraw, readhalf):
    assert msg[:8] == preamble,\
        "LIDAR status packet "+','.join((str(ord(char)) for char in msg[:8]))
        
    angle = ord(msg[20])*256 + ord(msg[21])
    if readraw:
        return angle, msg[8:]
        
    firinglist = (msg[f+20:f+22]+msg[f+24:f+56]+msg[f+120:f+128]
                        for f in firingidxlist)
    if readhalf:
        return angle, ''.join(firinglist)
    
    # not completed
    #firingdata = (struct.unpack(packedstructure, f) for f in firinglist)
    #return angle, list(firingdata)


""" The class that should be used to log LIDAR data. It should be placed in
    a with statement, but you still have to call start(). start() can optionally
    pause the main thread to wait for the first LIDAR message, because it takes
    at least ten seconds to start up.  However, either way the logged times are
    based on the computer's timer and the provided referenceTime, so they will
    not be out of sync.
"""
class Lidar(Process):
    def __init__(self, IP, filename, readtype = 'half', waitOnStart=False):
        self.logfile = open(filename, 'w')
        self.loglist = []
        self.angle = 0
        self.log_buffer_size = 1000 # only write this often
        self.readraw = readtype == 'raw'
        self.readhalf = readtype == 'half'
        assert readtype in ('raw','half'), "readtype not implemented"
        self.wait = waitOnStart
        
        self.socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        print "connecting to LIDAR..."
        self.socket.connect((IP, 4141))
        print "LIDAR connected"
        Process.__init__(self)
        
    
    def start(self, referenceTime):
        self.startTime = referenceTime
        if self.wait: # pause main thread 
            self.awaitMessage()
        Process.start(self)
        
    def run(self):
        msg = ''
        loglen = 0
        if not self.wait:
            self.awaitMessage() # pause helper thread
        while True:
            while len(msg) < 6632:
                msg += self.socket.recv(4096)
            angle, newread = _readFromLidar(msg[:6632], self.readraw, self.readhalf)
            msg = msg[6632:]
            
            if angle < self.angle: # save time (roughly) once per rotation
                self.loglist += [self.getTime()]
            self.angle = angle
            self.loglist += [newread]
            loglen += 1
            
            if loglen >= self.log_buffer_size:
                self.logfile.write(''.join(self.loglist))
                self.loglist = []
                loglen = 0

    ## pauses until the LIDAR is actually sending data
    def awaitMessage(self):
        print("waiting for first LIDAR packet...")
        ready_to_read, ready_to_write, in_error = select.select(
              (self.socket,), [], [], 30.)
        assert len(ready_to_read) > 0, "LIDAR not running within 30 seconds"
        print("LIDAR sending packets")
                
    def getTime(self):
        return 'NEWTIME{:9.3f}'.format(time.time() - self.startTime)
            
    def terminate(self):
        self.socket.close()
        self.logfile.close()
        Process.terminate(self)
        
    def __enter__(self):
        return self
    def __exit__(self, errtype, errval, traceback):
        self.terminate()
        
        
""" reads LIDAR data from the Lidar class and processes into seperate numpy
    arrays for each full rotation. """
def processLidarFile(infilename, outfolder, readtype = 'half', writetype='track'):
    assert readtype in ('half','raw')
    assert writetype in ('track','HVIR')
    
    if writetype == 'track':
        outarray = np.zeros((0,17))
    elif writetype == 'HVIR':
        outarray = np.zeros((0,4))
    currtime = ''
    fullpackedstructure = ">" + ("H"+"L"*8+"B"*8)*50
    
    with open(infilename, 'r') as infile:
        while True:
            
            # check for new time
            msg = infile.read(16)
            if len(msg) < 16: break
            if msg[:7] == 'NEWTIME':
                currtime = msg[7:].replace(' ','0')
                prefix = ''
            else:
                prefix = msg
        
            if readtype=='raw':
                msg = prefix + infile.read(6624-len(prefix))
                if len(msg) < 6624: break
                firinglist = (msg[f+20:f+22]+msg[f+24:f+56]+msg[f+120:f+128]
                        for f in firingidxlist)
                firingdata = [struct.unpack(packedstructure, f) for f in firinglist]
            
            elif readtype=='half':
                msg = prefix + infile.read(2100-len(prefix))
                if len(msg) < 2100: break
                firinglist = struct.unpack(fullpackedstructure, msg)
                firingdata = zip(*[iter(firinglist)]*17) # trick to reshape list
        
            # convert to standard values
            firingdata = np.array(firingdata, dtype=float)
            firingdata[:,0] = firingdata[:,0] * angle_conversion # to radians
            firingdata[:,1:9] = firingdata[:,1:9] * distance_conversion # to meters
            
            if writetype == 'HVIR': # one track per row
                angles = np.repeat(firingdata[:,0], 8)
                dists = firingdata[:,1:9].ravel()
                intensities = firingdata[:,9:].ravel()
                vert = np.tile(vertical_angles, firingdata.shape[0])
                firingdata = np.array((angles,vert,dists,intensities)).T
            
            outarray = np.append(outarray, firingdata, axis=0)
                
            # check if a rotation has been completed
            anglechange = np.where(np.diff(outarray[:,0])<0)[0]
            assert len(anglechange) < 2 # shouldn't have completed multiple
            if len(anglechange) == 1:
                cutoff = anglechange[0]
                # save to a new file
                if currtime != '': # don't save initial, incomplete rotation
                    np.save(outfolder+'/'+currtime, outarray[:cutoff,:])
                outarray = outarray[cutoff+1:,:]
                
        
        
""" test by saving to file for 60 seconds """
if __name__ == '__main__':
#    with Lidar('129.116.100.217', 'lidar.dat', readtype='half',
#               waitOnStart=True) as lidar:
#        lidar.start(time.time())
#        time.sleep(60.)
    processLidarFile('lidar.dat','testoutput', writetype='HVIR')
