# annie-rose
## Examples
### Bobwire

This example is a very basic quantum seal demonstration. In it, Alice normally sends a |Phi+> state to Bob, but after a certain number of states, transmits randomly modulated Bell States. This is interpreted by Bob as noise or an intrusion. This example shows how more sophisticated client applications can be built that utilize the simulation framework. In this case, Bob plots real-time values for the bit error rate (BER) of measurements in both the X and Z basis.

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
As soon as you enter Alice's command, you should begin to see output on Bob's plots.


#### Files
##### `app.py`
Excluding Open vSwitch, this script is what launches the interactable simulation. The network topology file is parsed and passed into the network simulator. The software for each host is launched within their own namespace, and by using IPC through the /tmp location, quantum simulation traffic is routed without traversing and impacting the simulated network. The script also installs specific quantum flows to the switch, allowing circuit switched quantum network traffic.


##### `3host.json`
A JSON representation of the network topology.

##### `lib/a_qim_client.py`
A host script for communicating classical data with superdense coding. This file is for transmission, where quantum states are sent to Bob.

##### `lib/b_qim_client.py`
A host script for communicating classical data with sueprdense coding. This file is for reception, where quantum states are received from Alice.
