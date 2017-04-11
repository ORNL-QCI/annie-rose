import orsoqs
import json
import signal
import sys
import threading
import matplotlib.pyplot as plt
import numpy as np
import zmq
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

class qim_client:
    def sdc_encode_char(self, c):
        '''
        Encode a character into SDC flags.
        '''
        c = ord(c)
        ret = str((c & 0x03) >> 0) + \
                str((c & 0x0c) >> 2) + \
                str((c & 0x30) >> 4) + \
                str((c & 0xc0) >> 6)
        
        return ret
    
    def sdc_encode_str(self, s):
        '''
        Encode a string of characters into SDC flags.
        '''
        return ''.join([self.sdc_encode_char(c) for c in str(s)])
    
    def sdc_decode_char(self, b):
        '''
        Decode a character from SDC flags.
        '''
        if len(b) != 4:
            raise ValueError('Length of b not 4')
        
        b = [int(x) for x in b]
        return chr((b[0] << 0) \
                   + (b[1] << 2) \
                   + (b[2] << 4) \
                   + (b[3] << 6)
                  )
    
    def sdc_decode_str(self, s):
        '''
        Decode a string from SDC flags.
        '''
        if len(s) % 4 != 0:
            raise ValueError('Length of s not multiple of 4')
        
        ret = ''
        for i in range(0, len(s), 4):
            ret += self.sdc_decode_char(s[i:i+4])
        return ret
    
    def get_basis(self):
        if(self.basisLoc == 7):
            self.basisLoc = 0
            self.basis = ord(self.bases.read(1))
        
        ret = (self.basis >> self.basisLoc) & 1
        self.basisLoc += 1
        return ret
    
    def listen_cb(self, msg):
        '''
        A really simple callback function that saves what is received.
        '''
        if msg[-1] == '\0':
            msg = msg[:-1]
        
        response = json.loads(msg)
        
        if 'error' in response and response['error'] == True:
            raise Exception('Failure in listen_cb()')
        elif 'result' in response:
            meas = int(response['result'])
            ber = 0
            bas = 'x'
            if meas == 1 or meas == 2:
                ber = 1
            if self.get_basis() == 1:
                bas = 'z'
            self.ber.put([bas, ber])
            return '_'
        else:
            raise Exception('Failure in listen_cb()')
    
    def plotter(self):
        datal = 25
        windowl = 100
        xdata = [0]*datal
        zdata = [0]*datal
        xwindow = [0]*windowl
        xewindow = [0]*windowl
        zwindow = [0]*windowl
        zewindow = [0]*windowl
        plt.ion()
        x = range(1,windowl+1)
        y = [0]*windowl
        fig, ((ax, az), (axe, aze)) = plt.subplots(2, 2, figsize=(10,5))
        ax.set_ylim([0, 1])
        az.set_ylim([0, 1])
        axe.set_ylim([0, 1])
        aze.set_ylim([0, 1])
        line1, = ax.plot(x, y, 'b.')
        line2, = az.plot(x, y, 'b.')
        line1e, = axe.plot(x, y, 'b.')
        line2e, = aze.plot(x, y, 'b.')
        # this is very inefficient
        while True:
            # ('x', 'val')
            item = self.ber.get()
            if item[0] == 'x':
                xdata = xdata[1:] + [item[1]]
                xwindow = xwindow[1:] + [np.mean(xdata)]
                line1.set_ydata(xwindow)
                xewindow = xewindow[1:] + [np.std(xdata)]
                line1e.set_ydata(xewindow)
                
                zwindow = zwindow[1:] + [-100]
                line2.set_ydata(zwindow)
                zewindow = zewindow[1:] + [-100]
                line2e.set_ydata(zewindow)
            else:
                zdata = zdata[1:] + [item[1]]
                zwindow = zwindow[1:] + [np.mean(zdata)]
                line2.set_ydata(zwindow)
                zewindow = zewindow[1:] + [np.std(zdata)]
                line2e.set_ydata(zewindow)
                
                xwindow = xwindow[1:] + [-100]
                line1.set_ydata(xwindow)
                xewindow = xewindow[1:] + [-100]
                line1e.set_ydata(xewindow)
            fig.canvas.draw()
    
    def __init__(self, receiveCb, afIEndpoint, afOEndpoint, basesFile):
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.zcontext = zmq.Context(1)
        self.orclient = orsoqs.create_client()
        self.osocket = orsoqs.connect(self.orclient, afIEndpoint, orsoqs.CON_PUSH)
        self.isocket = orsoqs.connect(self.orclient, afOEndpoint, orsoqs.CON_WAIT)
        self.isocket.set_proc_callback(self.listen_cb)
        
        self.bases = open(basesFile)
        self.basisLoc = 0
        self.basis = ord(self.bases.read(1))
        
        self.ber = Queue()
        self.plotter = threading.Thread(target=self.plotter)
        self.plotter.start()
    
    def signal_handler(self, signum, frame):
        pass
    
    def send(self, address, msg):
        '''
        Send a message to a given address, where address is a numerical IP in
        network byte order.
        '''
        request = {
                'action' : 'push',
                'method' : 'tx',
                'parameters' : [
                    int(address),
                    int(14450),
                   ''.join([self.sdc_encode_str(msg)])
                ]
            }
        
        request = json.dumps(request)
        
        # We have automatic Python garbage collection from SWIG
        request = orsoqs.create_msg(request, len(request)+1)
        # send_msg() sends our message and returns a response message
        # str() creates a copy of the response message string
        response = orsoqs.send_msg(self.osocket, request).str()
        
        response = json.loads(response)
        
        if 'error' in response and response['error'] == True:
            return False
        elif 'result' in response and response['result'] == True:
            return True
        else:
            return False

test = qim_client(None, 'tcp://127.0.0.1:12346', 'tcp://127.0.0.1:12345', 'bases.bin')
signal.pause()
