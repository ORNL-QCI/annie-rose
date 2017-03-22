import orsoqs
import json
import signal
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
            print response['result']
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
test.send(167772675, "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed vel augue ut tellus finibus ullamcorper. Quisque quis justo egestas orci bibendum rutrum eu a felis. Curabitur et lorem turpis. Curabitur at diam auctor, aliquam ipsum ut, fermentum lacus. Duis ut lectus ut sem semper cursus. Donec bibendum aliquam vestibulum. Maecenas eget interdum nisl. In hac habitasse platea dictumst. Pellentesque mollis arcu metus, eu faucibus lorem molestie in. Pellentesque sed tortor nulla. In interdum libero magna, non efficitur felis placerat eu. Nam vel metus eros. Vivamus congue sapien nec ligula porttitor, sed accumsan magna hendrerit. Praesent vitae eleifend risus. Vivamus et mi non felis bibendum bibendum eget ut dui. Morbi non faucibus nulla, a consectetur dolor. Integer dui elit, ornare laoreet consequat et, auctor nec nisl. Aenean tincidunt diam rutrum, facilisis odio at, commodo ipsum. Aliquam facilisis, magna et bibendum semper, felis est vestibulum velit, et fringilla nunc metus aliquet diam. Nulla vitae mauris ut velit luctus pulvinar id maximus mauris. Duis in tristique erat. Pellentesque commodo turpis a odio interdum, dictum fringilla diam luctus. Duis et bibendum lectus. Integer euismod dolor quis nisl luctus sodales. Proin maximus ultricies leo ac sagittis. Morbi sollicitudin efficitur arcu eu pellentesque. Ut in metus cursus, luctus justo sed, porttitor erat. Quisque et dui pretium, consequat orci eu, ultrices justo. Integer consequat tortor urna, a iaculis nunc cursus ac. Ut faucibus fermentum pharetra. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Vestibulum iaculis, purus non maximus volutpat, diam nibh malesuada ante, ut vehicula libero leo quis sem. Phasellus at eros odio. Integer at enim commodo, finibus nibh id, varius tellus. Vivamus elit mi, semper nec auctor nec, iaculis mollis metus. Etiam tincidunt ex non iaculis convallis. Vestibulum mi massa, placerat quis varius id, lobortis eu felis. Suspendisse dapibus nulla vulputate sapien interdum rutrum. Quisque a tortor quis nisi tincidunt mollis. Nullam augue risus, gravida eu orci eget, feugiat sagittis arcu. Etiam tincidunt eu libero ut blandit. Fusce tincidunt augue et feugiat ornare. Fusce ac dolor massa. Suspendisse a faucibus turpis. Ut rutrum magna sit amet turpis tempus, sed ultricies ligula venenatis. Nam ligula neque, rhoncus nec urna semper, rhoncus finibus ipsum. Nullam commodo pretium aliquet. Fusce facilisis mi vel efficitur posuere. Maecenas tincidunt semper massa, et pretium felis euismod eu. Nunc tincidunt feugiat quam, id lacinia orci venenatis et. Integer malesuada vehicula consectetur. Etiam placerat, sapien vitae blandit rutrum, sem eros placerat lacus, ut consequat metus magna ut tortor. Aenean accumsan eros vel leo laoreet, et interdum nunc lobortis. Vestibulum mattis justo mauris, a dictum augue maximus ac. Mauris eu elementum ex. In non elementum lorem, non consectetur leo. Sed pulvinar dapibus diam, at euismod libero posuere eget. Phasellus ornare, mauris sit amet interdum laoreet, dui quam egestas nunc, non fringilla nibh magna id eros. Proin sed aliquam justo. Integer dui neque, pretium sit amet mi sed, ultrices ornare quam. Duis rhoncus condimentum ex sit amet interdum. Phasellus consectetur dolor justo, non venenatis risus semper fringilla. Sed vel justo et velit ornare feugiat eget at libero. Donec sit amet augue congue, placerat est consectetur, dignissim tortor. In vel lectus ex. Fusce ex libero, egestas ac interdum vitae, fringilla at orci. Suspendisse ultrices turpis at egestas dignissim. Pellentesque habitant morbi tristique senectus et netus et malesuada fames ac turpis egestas. Donec aliquet ex nec lorem auctor aliquet laoreet luctus arcu. Aliquam ut ex ac orci maximus varius. Integer tortor lacus, sollicitudin sit amet mi in, dictum placerat lectus. In hac habitasse platea dictumst. Vivamus nunc nibh, vestibulum vel pharetra ac, ornare sit amet quam. Vivamus pulvinar egestas arcu a condimentum. Aliquam tristique elit ex, vel lacinia augue pretium varius.")
