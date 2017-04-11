import orsoqs
import json
import threading
import random
import signal
import struct
import zmq

class qim_client:
    def listen_cb(self, msg):
        '''
        A really simple callback function that prints what is received.
        '''
        msg = json.loads(msg)
        
        if 'error' in response and response['error'] == True:
            raise Exception('Failure in listen_cb()')
        elif 'result' in response:
            outstr += str(self.sdc_decode_str(self.sbuf))
            return 'returned string'
        else:
            raise Exception('Failure in listen_cb()')
    
    def __init__(self, receiveCb, afIEndpoint, afOEndpoint):
        signal.signal(signal.SIGINT, self.signal_handler)
        
        self.zcontext = zmq.Context(1)
        self.orclient = orsoqs.create_client()
        self.osocket = orsoqs.connect(self.orclient, afIEndpoint, orsoqs.CON_PUSH)
        self.isocket = orsoqs.connect(self.orclient, afOEndpoint, orsoqs.CON_WAIT)
        self.isocket.set_proc_callback(self.listen_cb)
    
    def signal_handler(self, signum, frame):
        pass
    
    def sdc_encode_char(self, c):
        '''
        Encode a character into SDC flags.
        '''
        c = ord(c)
        ret = str((c & 0x03) >> 0) \
                  + str((c & 0x0c) >> 2) \
                  + str((c & 0x30) >> 4) \
                  + str((c & 0xc0) >> 6)
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
    
    def send(self, address, msg):
        '''
        Send a message to a given address, where address is a numerical IP in network byte
        order.
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

test = qim_client(None, 'tcp://127.0.0.1:12346', 'tcp://127.0.0.1:12345')

instr = struct.pack('I', 0)*10
for _ in range(0, 5):
    byte = 0
    for i in range(0, 4):
        if random.choice(range(0,99)) < 10:
            continue
        r = random.choice([0,3])
        byte = byte | (r << i*2)
    instr += struct.pack('I', int(byte))
instr += struct.pack('I', 0)*10
test.send(167772675, instr)
