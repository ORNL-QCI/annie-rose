import json
import os
from subprocess import Popen, call
import sys
from time import sleep
from mininet.net import Mininet
from mininet.node import Controller, RemoteController, OVSController
from mininet.node import CPULimitedHost, Host, Node
from mininet.node import OVSKernelSwitch, UserSwitch, OVSSwitch
from mininet.node import IVSSwitch
from mininet.log import setLogLevel, info
from mininet.link import TCLink
from mininet.cli import CLI

# Ryu script
RYU_SCRIPT = '/home/annie/ryu/ryu/app/simple_switch_14.py' 

# A client's qPort
clientAFQPort = '14450'

# A client's AF receive endpoint
clientAFRxEndpoint = 'tcp://127.0.0.1:12345'

# A client's AF transmit endpoint
clientAFTxEndpoint = 'tcp://127.0.0.1:12346'

##########
# Debug
##########
debugSabot = False
debugSabotExtra = '--tool=cachegrind'
debugSabotFile = 'SABOT'

debugDispatcher = False
debugDispatcherExtra = '--leak-check=full'
debugDispatcherFile = 'ED'

debugArmishFireplace = False
debugArmishFireplaceExtra = '-v'#'--leak-check=full'
debugArmishFireplaceFile = 'AF'

def get_client_af_string(endpoint, rxDispatcherEndpoint, txDispatcherEndpoint):
    '''
    Construct the string list to call armish-fireplace for a client.
    '''
    puParams = '--e {}:{} --rd {} --td {}'.format(endpoint,
                                                  clientAFQPort,
                                                  rxDispatcherEndpoint,
                                                  txDispatcherEndpoint)
    af = ['armish-fireplace',
          '-o', clientAFRxEndpoint,
          '-i', clientAFTxEndpoint,
          '-m', 'brazil',
          '-t', 'trx_circuit',
          '-u', puParams]
    
    if debugArmishFireplace:
        af.insert(0, '--log-file={}-{} {}'.format(debugArmishFireplaceFile,
                                                  endpoint,
                                                  debugArmishFireplaceExtra))
        af.insert(0, 'valgrind')
    
    return af

def get_switch_af_string(endpoint, AFrx, AFtx, txDispatcherEndpoint):
    '''
    Construct the string list to call armish-fireplace for a qswitch.
    '''
    puParams = '--e {} --p 3 --td {}'.format(endpoint, txDispatcherEndpoint)
    af = ['armish-fireplace',
          '-o', 'ipc:///tmp/qs2',
          '-i', 'ipc:///tmp/qs1',
          '-m', 'trabea',
          '-t', 'circulator_switch',
          '-u', puParams]
    
    if debugArmishFireplace:
        af.insert(0, '--log-file= {}-{} {}'.format(debugArmishFireplaceFile,
                                                   endpoint,
                                                   debugArmishFireplaceExtra))
        af.insert(0, 'valgrind')
    return af

def launch_qsim_backend(node=None, **args):
    '''
    Launch qsim backend on a mininet node or in the current namespace.
    
    Returns a list of instances from popen.
    '''
    sabot = ['sabot',
             '-e', str(args['sabotEndpoint']),
             '-t', str(args['sabotThreadCount'])]
    if debugSabot:
        sabot.insert(0, '--log-file={} {}'.format(debugSabotFile,
                                                  debugSabotExtra))
        sabot.insert(0, 'valgrind')
    
    eldispacho = ['eldispacho',
                  '--rs', str(args['dispatcherRxEndpoint']),
                  '--ts', str(args['dispatcherTxEndpoint']),
                  '--s', str(args['dispatcherSabotEndpoint']),
                  '--st', str(args['dispatcherThreadCount']),
                  '-t', str(args['dispatcherTopology'])]
    if 'dispatcherLoggerEndpoint' in args:
        eldispacho.extend(['-l', str(args['dispatcherLoggerEndpoint'])])
    if debugDispatcher:
        eldispacho.insert(0, '--log-file={} {}'.format(debugDispatcherFile,
                                                       debugDispatcherExtra))
    
    instanceList = list()
    launchF = Popen if node is None else none.popen
    instanceList.append(launchF(sabot))
    instanceList.append(launchF(eldispacho))
    
    return instanceList

def generate_topology(net, topoJson, controller):
    '''
    Generate a topology inside net with controller.
    '''
    def ip_2_str(ip):
        '''
        Convert a list of 4 octets to dot-decimal notation.
        '''
        assert(len(ip) == 4)
        return '.'.join([str(x) for x in ip])
    
    def ipstr2num(s):
        '''
        Convert dot notation IP string to numeric.
        '''
        return sum([(int(x) << 8*(3-idx)) for idx,x in enumerate(s.split('.'))])
    
    def inc_ip(lastIP):
        lastIP[3] = lastIP[3] + 1
        return lastIP
    
    # The IP range given in the net object
    baseIP = [int(x) for x in net.ipBase.split('/', 1)[0].split('.')]
    # An incrementer used when adding hosts to the net object
    lastIP = baseIP
    # List of switch objects for classical switches
    cSwitches = []
    # List of node objects for quantum switches
    qSwitches = []
    # List of node objects for hosts
    hosts = []
    # List of links between node objects in the classical plane
    cLinks = []
    # List of links between node objects in the quantum plane
    qLinks = []
    
    for switchObject in topoJson['switches']:
        # Add classical part of switch
        cSwitch = net.addSwitch(switchObject['name'], cls=OVSSwitch)
        cSwitches.append(cSwitch)
        
        if 'isQuantum' in switchObject and switchObject['isQuantum'] is False:
            # Only a classical switch
            info('*** Switch: ' + switchObject['name'])
            continue
        
        # Generate IP of qswitch node
        lastIP = inc_ip(lastIP)
        qSwitchIP = ip_2_str(lastIP)
        
        # Add quantum part of switch
        qSwitch = net.addHost('q'+switchObject['name'], cls=Host, ip=qSwitchIP)
        qSwitches.append(qSwitch)
        
        # Add link between classical part of switch and quantum part of switch
        net.addLink(cSwitch, qSwitch)
        
        info('*** Switch: {}; q{} at {}\n'.format(switchObject['name'],
                                                  switchObject['name'],
                                                  qSwitchIP))
    for hostObject in topoJson['hosts']:
        # Generate IP of the host
        lastIP = inc_ip(lastIP)
        hostIP = ip_2_str(lastIP)
        
        # Add host
        host = net.addHost(hostObject['name'], cls=Host, ip=hostIP)
        hosts.append(host)
        
        info('*** Host: {} at {}\n'.format(hostObject['name'], hostIP))
    
    for link in topoJson['connections']:
        # Add link between two nodes
        endpointA = net.get(link['endpointA'])
        endpointB = net.get(link['endpointB'])
        net.addLink(endpointA, endpointB)
        cLinks.append([endpointA, endpointB])
        
        info('*** Link: {} <-> {}'.format(endpointA.name, endpointB.name))
        
        quantumEA = link['endpointA']
        quantumEB = link['endpointB']
        if any(d['name'] == link['endpointA'] for d in topoJson['switches']):
            quantumEA = 'q' + quantumEA
        if any(d['name'] == link['endpointB'] for d in topoJson['switches']):
            quantumEB = 'q' + quantumEB
        if quantumEA is not link['endpointA'] or quantumEB is not link['endpointB']:
            qLinks.append([net.get(quantumEA), net.get(quantumEB)])
            info('; {} <~> {}\n'.format(quantumEA, quantumEB))
    
    # Create mininet topology
    net.build()
    # Start the controller
    controller.start()
    
    for switch in cSwitches:
        # Connect the switch to our controller
        switch.start([controller,])
        # Set our switch to use OF 1.4
        switch.cmd('ovs-vsctl set Bridge ' + switch.name + ' protocols=OpenFlow14')
    # Take the edge off
    sleep(1)
    
    simIP = ''
    dispatcherTxEndpoint = 'ipc:///tmp/dispatcher_tx'
    dispatcherRxEndpoint = 'ipc:///tmp/dispatcher_rx'
    dispatcherTopologyJson = {
        'nodes': [
            {
                'model' : 'client',
                'id' : ipstr2num(host.IP())
            } for host in hosts
        ],
        'connections': [
            {
                'endpoints' : [
                    ipstr2num(link[0].IP()), ipstr2num(link[1].IP())
                ]
            } for link in qLinks
        ]
    }
    for item in qSwitches:
        jItem = next(a for a in topoJson['switches'] if a['name'] == item.name[1:])
        newSwitchItem = {}
        newSwitchItem['model'] = str(jItem['model'])
        newSwitchItem['id'] = ipstr2num(item.IP())
        if 'ports' in jItem:
            newSwitchItem['portCount'] = jItem['ports']
            if newSwitchItem['portCount'] < len(jItem['connections']):
                raise ValueError('port value smaller than connection count for switch ' + item.name[1:])
        else:
            newSwitchItem['portCount'] = len(jItem['connections'])
        newSwitchItem['ports'] = [ipstr2num(net.get(host).IP()) for host in jItem['connections']]
        
        dispatcherTopologyJson['nodes'].append(newSwitchItem)
    
    dispatcherTopology = json.dumps(dispatcherTopologyJson)
    quantumBackend = launch_qsim_backend(None,
            sabotEndpoint = 'ipc:///tmp/sabot',
            sabotThreadCount = 1,
            dispatcherSabotEndpoint = 'ipc:///tmp/sabot',
            #dispatcherLoggerEndpoint = 'ipc:///tmp/eldispacho_dspy', # This enables logging using dspy (Greatly increases CPU usage)
            dispatcherTxEndpoint = dispatcherTxEndpoint,
            dispatcherRxEndpoint = dispatcherRxEndpoint,
            dispatcherThreadCount = 1,
            dispatcherTopology=dispatcherTopology)
    sleep(.5)
    switchAFList = []
    switchAFList.append(
        qSwitches[0].popen(
            get_switch_af_string(qSwitches[0].IP(),
                                 'tcp://{}:12345'.format(qSwitches[0].IP()),
                                 'tcp://{}:12346'.format(qSwitches[0].IP()),
                                 dispatcherTxEndpoint)))
    clientAFList = []
    for client in hosts:
        clientAFList.append(
            client.popen(
                get_client_af_string(client.IP(),
                                     dispatcherRxEndpoint,
                                     dispatcherTxEndpoint)))
    sleep(.5)
    return [net, quantumBackend, switchAFList, clientAFList]

setLogLevel('info')
controllerP = Popen(['exec ryu-manager --ofp-tcp-listen-port 6633 '+RYU_SCRIPT+' > CONTROLLER_LOG 2>&1'], shell=True)
sleep(1)
controllerab = RemoteController(name='c0',
                                controller=Controller,
                                protocol='tcp',
                                port=6633)

net = Mininet(topo=None,
              build=False,
              ipBase='10.0.2.0/24',
              link=TCLink)

topoFile = open('3host.json')
topoJson = json.loads(topoFile.read())
topoFile.close()

topoOutput = generate_topology(net, topoJson, controllerab)
net = topoOutput[0]

#
#
# Install quantum flows on switch.
# 
# This prevents us from having to hardcode this stuff in the controller.
#
#
#

# dl_type=2048		= ipv4
# nw_proto=6		= tcp
# tp_dst=14450		= tcp dest. port 14450
# dl_type=2048,nw_proto=6 = tcp
#proto_ver = 0,
#options = 2 ???
qsFlowBase = 'ovs-ofctl add-flow s0 -O OpenFlow14 "priority=11,tcp,tcp_{}=14450,tcp_flags=+psh,in_port={},dl_dst={},action=qscon:(0;2;{};{};ipc:///tmp/qs1),output:{}"'

# ({'src', 'dst'}, cin_port, dest_mac, qin_port, qout_port, cout_port)
net.get('alice').cmd(qsFlowBase.format('src', 2, net.get('bob').MAC(), 0, 1, 3))
net.get('alice').cmd(qsFlowBase.format('dst', 2, net.get('bob').MAC(), 0, 1, 3))
net.get('alice').cmd(qsFlowBase.format('src', 3, net.get('alice').MAC(), 1, 0, 2))
net.get('alice').cmd(qsFlowBase.format('dst', 3, net.get('alice').MAC(), 1, 0, 2))

# Fill out rest of MAC table in controller
net.get('alice').cmd('ping ' + net.get('bob').IP() + ' -c 3')
net.get('bob').cmd('ping ' + net.get('charlie').IP() + ' -c 3')

CLI(net)

#####
info('*** Stopping client quantum software\n')
for af in topoOutput[3]:
    while af.returncode is None:
        af.terminate()
        af.poll()
        sleep(0.05)

#####
info('*** Stopping quantum simulator backend\n')
# Currently, the dispatcher doesn't respond to SIGINT, so we use KILL here.
# Eventually, we want to change to terminate
for i in topoOutput[1]:
    i.kill()

#####
info('*** Stopping quantum switch software\n')
for af in topoOutput[2]:
    while af.returncode is None:
        af.terminate()
        af.poll()
        sleep(0.05)

#####
info('*** Stopping controller\n')
while controllerP.returncode is None:
    controllerP.kill()
    controllerP.poll()
    sleep(0.05)
