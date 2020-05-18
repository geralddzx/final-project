# Project 7: Congestion Aware Load Balancing

Implementing the [CONGA](https://people.csail.mit.edu/alizadeh/papers/conga-sigcomm14.pdf) load balancing algorithm.

## Overview

In project 3, you used ECMP to solve problems of network congestion by distributing flows across multiple paths. However, ECMP does not fully solve network congestion. Since ECMP doesn't take into account the size of the flows, if multiple large flows are concentrated on one path, then congestion becomes a problem. The goal of this project is to address this issue of congestion.

We will use the fact the P4 allows for the reading of queuing information (i.e. for example how many packets are waiting to be transmitted) to detect congestion(i.e. if a queue contains many packets). If congestion is detected, then the flow should be moved to another path.

Specifically, if an egress (switch right before the destination host) identifies that the packet has experienced congestion, then it will sent a notification message to the ingress switch of the packe. Upon receiving the message, the switch will randomly move the flow to another path. Obviously, this is by far not the best way of exploring available paths, but it will be enough to show how to collect information as packets cross the network, how to communicate between switches, and how to make them react to network states.

<!As a starting point for this exercise, we use the code from last week's simple router (you can use the solution that we provide in the skeleton or your own code, if you managed to
solve it). In this exercise we might use more than one topology, so using the `routing-controller.py` from the previous exercise will come very handy.!>

## Before starting

### nload

You will have to install a new tool we will use during the exercise:

`nload`: a console application which monitors network traffic and bandwidth usage in real time.

   ```bash
   sudo apt-get install nload
   ```

### What is provided

**Topologies**:
  *  `topology/p4app-line.json`: describes a linear topology that will be used for our first test.
  *  `topology/p4app-medium.json`: describes a simple topology with multiple paths
  *  `topology/p4app_fattree.json`: describes the Fattree topology

**P4**:
  *  `p4src/loadbalancer.p4`: p4 file from solution of `ecmp` project as a starting point.

**Controller**:
  *  `routing-controller.py`: routing controller that fills in the forwarding tables and  ecmp tables as a starting point.

**Tools**:
  *  `apps/send.py`: a python script to generate tcp probe packets to read queues.
  *  `apps/receive.py`: a python script to receive tcp probes that include a `telemetry` header.
  *  `nload_tmux_*.sh`: scripts that will create a tmux window, and `nload` in different panes.
  *  `apps/send_traffic_*.py`: python scripts that use `iperf` to automatically generate flows to test our solution.

### New configuration fields in p4app.json

In this exercise you will find two configuration fields: `exec_scripts` and `default_bw` (inside the topology description).

1. `exec_scripts`: it allows you to add scripts that will be automatically called after the topology starts. The scripts will be called in the `root` namespace, not inside any host. For
example in the provided topologies, we use this field to call the `routing-controller.py` every time you start (or reboot) the topology. Thus, you don't have to run the controller manually anymore.
If for debugging reasons you want to start the controller yourself just remove this option (setting `reboot_run` to false does not suffice).

2. `default_bw`: you can see we used this option inside the `topology` description. This can be used to set the bandwidth of all the links in the topology. In this exercise, we are setting
them to `10mbps`.

### Notes about the topology file

For this exercise we will use the `l3` assignment strategy. Unlike the `mixed` strategy where hosts connected to the same
switch formed a subnetwork and each switch formed a different domain. In the `l3` assignment, we consider switches to only work
at the layer 3, meaning that each interface must belong to a different subnetwork. If you use the namings `hY` and `sX` (e.g h1, h2, s1, s2...),
the IP assignment will go as follows:

   1. Host IPs: `10.x.y.2`, where `x` is the id of the gateway switch, and `y` is the host id.
   2. Switch ports directly connected to a host: `10.x.y.1`, where `x` is the id of the gateway switch, and `y` is the host id.
   3. Switch to Switch interfaces: `20.sw1.sw2.<1,2>`. Where `sw1` is the id of the first switch (following the order in the `p4app` link definition), `sw2` is the
   id of the second switch. The last byte is 1 for sw1's interface and 2 for sw2's interface.

It is very important to note that actually `p4-utils` will not assign those IPs to the switches, but it will save them so they can be `virtually` used for some switch functionality (we will see what this means later).

You can find all the documentation about `p4app.json` in the `p4-utils` [documentation](https://github.com/nsg-ethz/p4-utils#topology-description).

### Notes about the P4 tables and the controller

In this exercise, we provide you with a basic version of ECMP implementation, with `ecmp_group` integrated. You may delete this field in project 3 for convenience, but you need to understand it in this project.

#### ECMP Group ####

In project 3, you implement ECMP for fattree topology. What if it is required to implement ECMP for any topology? You cannot simply assume that each packet could randomly be forwarded to one of the two ports in Fattree, and you cannot put different rules in the P4 table based on whether the packet should be forwarded up to the core switch or be forwarded down to a host in the pod.

ECMP group could be used here. In this project, you can find the controller `controller/routing-controller.py`, which implement a generic version of ECMP.
Here is how the controller implement ECMP: Given a switch and a host, if the destination of the arriving packet is the host, then the switch first finds out the shortest paths to that host. If there is only one path, then the controller will directly forward the packet to that path.
If there are multiple shortest paths, then those paths form a **ECMP group**.
The controller will map this packet with the ID of the ECMP group, and let the `ecmp_group_to_nhop` table to process it.
Then for each ECMP group, the controller then fills in the table `ecmp_group_to_nhop` so that the switch can forward the packet to the port corresponding to the ECMP hashing value.
You can check the code in the controller to understand it more.

Note that because we are using L3 assignment strategy, the IPv4 table in the P4 switch uses `lpm` mode for the key. We have implemented the ECMP routing algorithm and the basic tables in the P4 codes, and you do not need to modify them.

### Topologies

In this project, you may use the following three topology.

**Linear topology**. It consists of three switches forming a line. The first switch and the last switch both have two connected hosts.

**Medium topology**. It consists of 6 switches and 8 hosts. Switch `s1` and `s6` both have four connected hosts. Switch `s1` and `s6` are both connected to switch `s2`, `s3`, `s4`, and `s5`. Therefore, there are four paths between `s1` and `s6`, and the four paths are the same.

**Fattree topology**. The fattree topology used in previous projects.

## Observing the problem

Before starting the exercise, lets use the current code and observe how flows collide.

1. Start the medium size topology:

   ```bash
   sudo p4run --config p4app-medium.json
   ```

2. Open a `tmux` terminal (or if you are already usign `tmux`, open another window). And run monitoring script (`bash nload_tmux_medium.sh`). This script, will use `tmux` to create a window
with 4 panes, in each pane it will lunch a `nload` session with a different interface (from `s1-eth1` to `s1-eth4`), which are the interfaces directly connected to `h1-h4`.

   ```bash
   bash nload_tmux_medium.sh
   ```

3. Send traffic from `h1-h4` to `h5-h8`. There is a script that will do that for you automatically. It will run 1 flow from each host:

   ```bash
   sudo python send_traffic.py <time_to_send>
   ```

4. If you want to send 4 different flows, you can just run the command again, it will first stop all the `iperf` sessions, alternatively, if you want
to stop the flow generation you can kill them:

   ```bash
   sudo killall iperf
   ```

If each flow gets placed to a different path (very unlikely) you should get a bandwidth close to `9.5mbps` (remember, we set the link's bandwidth to that). For example,
after trying once, we got that 3 flows collide in the same path, and thus they get ~3mpbs, and one flow gets full bandwidth:

<p align="center">
<img src="images/example.png" title="Bandwidth example">
<p/>

The objective of this exercise is to provide the network the means to detect these kind of collisions and react.

## Detecting Congestion

Before implementing the real solution we will first do a small modification to the starting p4 program so to show how to read queue information. Some of the code
we will implement in this section will have to be changed for the final solution. Our objective in this example is to add the `telemetry` header if the packet
does not have it (first switch), and then update its `enq_qdepth` value setting it to the highest we find along the path.

1. First add a new header to the program and call it `telemetry`. This header will have two fields: `enq_qdepth` (16 bits) and `nextHeaderType` (16 bits, too). When added, this
header needs to be placed between the `ethernet` and `ipv4` (take that into account when you define the deparser).
2. Update deparser accordingly.
3. When packets carry the `telemetry` header, the `ethernet.etherType` has to be set to `0x7777`. Update the parser accordingly. Note, that the `telemetry` header
has a `nextHeaderType` that can be used by the parser to know which will be the next header. Typically `ipv4` (0x800).

4. All the queueing information is populated when the packet is enqueued by the traffic manager to its output port. Thus, the queueing information is only
available at the egress pipeline. In order to make this simple test work, you will have to implement the following logic at the egress pipeline:
    1. If the `tcp` header is valid, and the `tcp.dstPort == 7777` (trick we use to send probes, see [scapy sending script](./send.py)).
    2. If there is no `telemetry` header add it, and set the depth field to `standard_metadata.enq_qdepth` (which is the number of packets in the queue when this packet
    was enqueued, you can see all the queue metadata fields in the [v1model.p4](https://github.com/p4lang/p4c/blob/master/p4include/v1model.p4#L59). Modify the ethernet type to the one mentioned above, set the `nextHeaderType` to the ipv4 ethernet type.
    3. If there is already a `telemetry` header, set the depth field to the `standard_metadata.enq_qdepth` only if its higher.

At this point your switches should add the telemetry header to all the tcp packets with dst port 7777. This telemetry header will carry the worst queue depth found
across the path. To test if your toy congestion reader works do the following:

1. Start the linear topology, it has 3 switches connected in series, and 2 hosts connected to each extreme.

   ```bash
   sudo p4run --config p4app-line.json
   ```

2. Open a terminal in `h1` and `h3`. And run the send.py and receive.py scripts.

   ```bash
   mx h3
   python receive.py
   ```

   ```bash
   mx h1 python send.py 10.3.3.2 1000
   ```

  You should now see that the receiver prints the queue depth observed by the probes we are sending (packets with dst port == 7777). Of course, since we are not sending any traffic queues
  are always 0.

3. Run `send_traffic_simple.py` from the root namespace, you do not have to login into `h1`. This script will generate two flows from `h1` and `h2` to `h3` and `h4`. These two
flows will collide (since there is one single path). If you continue sending probes you should see how the queue fills up to 63 and starts oscillating (due to tcp nature).


<!-- ### Important note

In this introductory task you had to add an extra header (4 bytes) to just probe packets. In the next task you will do that for every single packet. This will have
a consequence you should we aware of. If a host sends a packet of size 9500 (the MTU of the links in the topology)  -->

## Keeping the telemetry in-network

In the previous section we were setting the telemetry header as the packet entered the network with a specific destination port and kept the telemetry header until the destination. We just did that for the sake of showing you how the queue depth changes as we make flows collide in one path.

In our real implementation, only switches from the inside the network will use the telemetry header to detect congestion and move flows. Thus, packets leaving the internal network (going to a host) should not have the telemetry header in them. Therefore, we need to remove it before the packet reaches a host.

To do that you will need to know which type of node (host or switch) is connected to each switch's port. As you have seen, to do something like that we need to use a table, the control plane and the topology object that knows how nodes are connected. In brief, in this section you have to:

1. Define a new table and action in the ingress pipeline, that will be used to know which output port the packet is going to. This table should match to the `egress_spec`. And call an action that sets to which type of node the packet will be going to (save that in a metadata field). For example you can use the number 1 for hosts and 2 for switches.
2. Modify the `routing-controller.py` program such that it fills this table. You can do that by writing inside the `set_egress_type_table` function. For each switch you should populate
the table with a port and the node type is connected to (host(1) or switch(2)).

3. Apply this table at the ingress control after when `egress_spec` is already known.

4. Modify the egress code you implemented before:
    1. Do not check for the tcp port 7777 anymore (remove that part of the code, for the final real implementation).
    2. If the telemetry header is valid and the next hop is a switch: Update the `enq_qdepth` field if its bigger than the current one.
    3. If the telemetry header is valid but the next hop is a host: Remove the `telemetry` header, and set the `etherType` to `ipv4` one.
    4. If there is no telemetry header and the next hop is a switch: Add the `telemetry` header, set the depth field, nextHeaderType and set the ethernet type to 0x7777.

At this point, for each tcp packet that enters the network, your switches should add the telemetry header and remove it when exiting to a host. To test that this is working you can
send tcp traffic and check with wireshark (monitoring an internal link) that indeed the ethernet header is `0x7777` and that the next 4 bytes belong to the `telemetry` header, and that
traffic exiting the network (going to hosts) look normal.

*Important:* due to adding extra bytes to packets you will not be able to run the `mininet> iperf` command anymore directly from the cli. If you do not specify it with an option (`-M`) iperf sends
packets that will use the maximum MTU size of the sender's output interface. Therefore, if hosts send packets with the maximum MTU, and then the first switch adds 4 bytes they will be dropped by the interfaces.
In our network created using `P4-utils` the mtu is set to 9500. You can see that the `send_traffic*` scripts we provide you tell iperf to not send packets bigger than 9000 bytes to avoid this problem.

## Congestion notification

In this section you will have to implement the egress logic that detects congestion for a flow, and send a feedback packet to the ingress switch (the switch this flow used to enter the network). To generate
a packet and send it to the ingress switch you will have to `clone` the packet that triggers the congestion, modify it and send it back to the switch.

Your tasks are:

1. You will have to extend the part in which egress switches remove the `telemetry` header. Now, the switch should also check if the received queue `depth` is above a
threshold. As default queues are 64 packets long, so use something between 30 and 60 as a threshold to trigger the notification message.

2. Upon congestion the switch will receive a burst of packets that would trigger the notification message. You can avoid that by adding a timeout per flow. For instance, every time you send a notification
message for flow X you save in a `register` the current time stamp. The next time you need to send a notification message, you check in the register if the time difference is bigger than some seconds (for example 0.5-1 seconds).

3. Furthermore, congestion events get usually created by the collision of multiple flows meaning that all of them will trigger notification messages. Moving all the flows to a new path can be suboptimal, you
may end up creating congestion in other paths and living the current one empty. Thus, sometimes its better if you don't move them all.  In order to do that, you could move them with
a probability p (i.e., 33%). You can use the random extern to decide if the flow needs to be notified.

4. If all the conditions above are true. You will have to send a packet notifying the ingress switch that this flow is experiencing congestion. To do that you need to generate a new packet out of the one you are forwarding. You can
do that by cloning the packet (you have to clone from egress to egress). Now if you remember when you clone a packet (check Failure Recovery and ARP Table exercise) you have to add a `mirroring_session` id which tells the switch to which port to
mirror the packet. Here you have two options:

   1. You define a `mirror_session` for each switch port.  For that you would need to use the `ingress_port` and a table that maps it to a mirror id that would send it to the port the packet came from.
   2. You clone the packet to any port (lets say port 1, it really does not matter). And then you recirculate it by using the `recirculate` extern. This will allow you to send this packet again to the ingress pipeline so you can use the normal forwarding
   tables to forward the packet. I recommend you to use this second option since it does not require an extra table and you make sure the packet is properly forwarded using the routing table.

5. Either if you use recirculation or just cloning, modify the ethernet type so your switches know that this packet is a notification packet (for example you can use 0x7778). Remember to update the parser accordingly.

**Hint 1:** if you want to easily be able to send the packet to the ingress switch you can just swap the IP addresses so the packet is sent to the originator host. This will make the packet be automatically routed to the ingress
switch (which it can then drop it).

**Hint 2:** In order to differentiate between `NORMAL`, `CLONED` and `RECIRCULATED` packets when you implement your ingress and egress logic remember to use the `standard_metadata.instance_type` metadata field. Check the
standard metadata [documentation](https://github.com/p4lang/behavioral-model/blob/master/docs/simple_switch.md#standard-metadata).

To test if your implementation is sending feedback notifications to the ingress switch, try to generate congestion (for example using the line topology and `send_traffic_simple.py` script) and check if these notification
packets are being sent to the ingress switch (filter packets using the special ethernet type you used for the notification packets).

## Trying new paths

In this section we will close the loop and implement the logic that makes ingress switches move flows to new paths. For that you have to:

1. For every notification packet that should be dropped at this switch (meaning that the current switch is sending it to a host). You have to update how the congested flow is hashed.

2. For that you will need to save in a `register` an ID value for each flow. Every time you receive a congestion notification for a given flow you will have to update the register value with a new id (use a random number). Remember that
the notification message has the source and destination IPs swapped so to access the register entry of the original flow you have to take that into account when hashing the 5-tuple to get the register index.

3. You will also need to update the hash function used in the original program (ECMP) and add a new field to the 5-tuple hash that will act as a randomizer (something like we did for flowlet switching).

4. Finally make sure you drop the congestion notification message.

`Note`: Remember to use the `standard_metadata.instance_type` to correctly implement the ingress and egress logic.

## Testing your solution

Once you think your implementation is ready, you should repeat the steps we showed at the beginning:

1. Start the medium size topology:

   ```bash
   sudo p4run --config p4app-medium.json
   ```

2. Open a terminal (or if you are usign `tmux`, open another window). And run monitoring script (`nload_tmux_medium.sh`). This script, will use `tmux` to create a window
with 4 panes, in each pane it will lunch a `nload` session with a different interface (from `s1-eth1` to `s1-eth4`), which are the interfaces directly connected to `h1-h4`.

   ```bash
   bash nload_tmux_medium.sh
   ```

3. Send traffic from `h1-h4` to `h5-h8`. There is a script that will do that for you automatically. It will run 1 flow from each host:

   ```bash
   python send_traffic.py 1000
   ```

4. If you want to send 4 different flows, you can just run the command again, it will first stop all the `iperf` sessions, alternatively, if you want
to stop the flow generation you can kill them:

   ```bash
   sudo killall iperf
   ```

This time, if your algorithm works, flows should start moving until eventually converging to four different paths. Since we are using a very, very simple algorithm
in which flows get just randomly re-hashed it can take some time until they converge (even a minute). Of course, this exercise was just a way to show you how to use the
queueing information to make switches exchange information and react autonomously. In a more advanced solution you would try to learn what is the occupancy of all the alternative
paths and just move flows if there is space.

## Test your solution in Fattree

In this section, we will test your solution in Fattree. Because your solution is generic, you do not need to modify any P4 codes and controller codes for a new topology. All you need to do is to replace the topology file and run it.

Your task in this section is to describe the performance difference between ECMP and your current implementation. You need to run the following commands:

1. Start the fattree topology

   ```bash
   sudo p4run --config p4app-fattree.json
   ```

2. Send traffic from `h1-h8` to `h9-h16`. There is a script that will do that for you automatically. It will run 1 flow from each host:

   ```bash
   python send_traffic_fattree.py 60
   ```

   You will run iperf for 60 seconds.

3. Check your results in `logs` directory. In this directory, you will find 8 files from `h1.log` to `h8.log`. Each file records the iperf throughput information for each iperf flow. 

4. Move to your project 3 repository and run the `send_traffic_fattree.py` there. Report the performance difference you find in `report/report.txt`.

## Submission and Grading

### What to Submit

You are expected to submit the following documents:

1. Code: The main P4 code should be in `p4src/include/headers.p4`, `p4src/include/parsers.p4`, and `p4src/loadbalancer.p4`;  The controller code should be in `controller/routing-controller.py` which fills in table entries when launching those P4 switches.

2. report/report.txt: You should describe the performance difference between ECMP and the implementation in this project in `report.txt`. 

### Grading

The total grades is 100:

- 20: For your description of how you program in `report.txt`.
- 80: We will check the correctness of your solutions for congestion aware load balancing.
- Deductions based on late policies


### Survey

Please fill up the survey when you finish your project.

[Survey link](https://docs.google.com/forms/d/e/1FAIpQLSfV649lR7bTRc14l71Mzb-vTVAZ7vY87vtwDrnxju5B6RB0NQ/viewform?usp=sf_link)
