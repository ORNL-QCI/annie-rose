# annie-rose
## Examples
### 3 Host

This example shows a basic 3 host network with each host connected to a quantum circulator switch. Although basic, this configuration permits transmission and reception between any host. The simulation is currently configured to transmit a long string of text from Alice to Bob, but this may be altered if desired.

Before running the example, you must load the Open vSwitch kernel module and launch the switch. Please refer to the proper documentation on information on how to do this. It's important to note that the Open vSwitch instance must be closed and relaunched after each example run, otherwise existing quantum flows may interfere with new ones.

To run the example, simply run the app.py using python:
```
# python app.py
```
After the setup is complete, you may execute scripts on the simulated hosts as would you on a real host. This is the great benefit of using Mininet: it allows a completely interactable simulation. To run the example, execute the following within the Mininet CLI:
```
bob xterm &
alice xterm
```
This will launch two instances of xterm, one for Alice and one for Bob. In Bob's xterm window, run his host script to listen for requests for quantum transmissions:
```
$ python lib/b_qim_client.py
```
and in Alice's xterm window, run her host script to transmit text through quantum transmission to Bob:
```
$ python lib/a_qim_client.py
```
As soon as you enter Alice's command, you should begin to see text output in Bob's terminal. This text has been transmitted through a simulated quantum channel using superdense coding. Since there is no noise model present, the transmission is perfect.



#### Files
##### `app.py`
Excluding Open vSwitch, this script is what launches the interactable simulation. The network topology file is parsed and passed into the network simulator. The software for each host is launched within their own namespace, and by using IPC through the /tmp location, quantum simulation traffic is routed without traversing and impacting the simulated network. The script also installs specific quantum flows to the switch, allowing circuit switched quantum network traffic.

##### `3host.json`
A JSON representation of the network topology.

##### `lib/qim_client.py`
A generic host script for quantum communication using superdense coding.

##### `lib/a_qim_client.py`
A host script for communicating classical data with superdense coding. This file is for transmission, where an example text is sent to Bob.

##### `lib/b_qim_client.py`
A host script for communicating classical data with sueprdense coding. This file is for reception, where an example text is received from Alice.
