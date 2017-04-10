
localport = 9002
IM_SIZE = (720,1280)
destport = 50001
destip = '127.0.0.1'



import connectors, time
import numpy as np
import cv2

data = ''
msg_size = IM_SIZE[0]*IM_SIZE[1]*3

rx = connectors.RxConnector(localport)
tx = connectors.TxConnector(destip, destport, 'TCP')
i = 0

with rx, tx:
    while(True):
        while len(data) < msg_size:
            data += rx.recv(4096)
        rx.ack()
        data = ''
        tx.send('Hello there hunny #{}'.format(i))
        tx.ack()
        i += 1
