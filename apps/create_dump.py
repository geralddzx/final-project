import os
import pdb
import csv
from dateutil.parser import parse

flows = {}

for filename in os.listdir("pcap"):
    command = "tcpdump -enn -r pcap/{} > pcap_dumps/{}".format(filename, filename)
    os.system(command)
