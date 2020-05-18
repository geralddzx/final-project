import os
import pdb
import csv
from dateutil.parser import parse
import matplotlib.pyplot as plt
import numpy as np

flows = {}

for filename in os.listdir("pcap_dumps"):
    with open("pcap_dumps/{}".format(filename), "r") as file:
        name = os.path.splitext(filename)[0]

        reader = csv.reader(file, delimiter = " ")
        for row in reader:
            src = row[1].split(":")
            dst = row[3].split(":")
            assert len(src) == 6
            assert len(dst) == 6
            flow = (row[1], row[3])
            flows.setdefault(flow, [])
            flows[flow].append((parse(row[0]), name))

for flow, times in flows.items():
    data = np.array(flows[flow]).T
    x = data[0]
    y = data[1]
    x = x[y.argsort()]
    y = y[y.argsort()]
    plt.title("source {} -> {} notification packets".format(flow[0], flow[1]))
    plt.scatter(x, y, marker = ".")
    plt.savefig("report/flows/{} notification packets.png".format('-'.join(flow)), bbox_inches="tight")
    plt.clf()
