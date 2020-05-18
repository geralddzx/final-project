import random
import time
from p4utils.utils.topology import Topology
from subprocess import Popen
import sys
import os
import shutil

topo = Topology(db="topology.db")

iperf_send = "mx {0} iperf -M 9000 -c {1} -t {2} --bind {3} -p {5} -i 5 2>&1 > logs/{6}.log"
iperf_recv = "mx {0} iperf -s -p {1} 2>&1 > /dev/null"
duration = int(sys.argv[1])

if os.path.exists('logs'): shutil.rmtree('logs')
os.makedirs('logs')

send_cmds = []
recv_cmds = []

Popen("sudo killall iperf", shell=True)

num_hosts = 16
num_senders= 8

for src_host in sorted(topo.get_hosts().keys(), key = lambda x: int(x[1:]))[:num_senders]:
    dst_host = 'h' + str((int(src_host[1:]) + 7) % num_hosts + 1)

    src_port = random.randint(1025, 65000)
    dst_port = random.randint(1025, 65000)
    src_ip = topo.get_host_ip(src_host)
    dst_ip = topo.get_host_ip(dst_host)

    send_cmds.append(iperf_send.format(src_host, dst_ip, duration, src_ip, src_port, dst_port, src_host))
    recv_cmds.append(iperf_recv.format(dst_host, dst_port))

#start receivers first
for recv_cmd in recv_cmds:
    print "Running:", recv_cmd
    Popen(recv_cmd, shell=True)

time.sleep(1)

for send_cmd in send_cmds:
    print "Running:", send_cmd
    Popen(send_cmd, shell=True)
