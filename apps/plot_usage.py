import os
import pdb
import csv
import re
from dateutil.parser import parse
import matplotlib.pyplot as plt
import numpy as np
import random


timestamps = []
names = []

for filename in os.listdir("pcap_dumps"):
    with open("pcap_dumps/{}".format(filename), "r") as file:
        name = os.path.splitext(filename)[0]

        reader = csv.reader(file, delimiter = " ")
        for row in reader:
            if re.match("[0-9][0-9]:[0-9][0-9]:[0-9][0-9].[0-9][0-9][0-9][0-9][0-9][0-9]", row[0]) and random.uniform(0, 1) < 0.01:
                assert(len(row[0]) == 15)
                timestamps.append(parse(row[0]))
                names.append(name)

x = timestamps
y = names
plt.title("packet distribution")
plt.scatter(x, y, marker = ".")
plt.savefig("report/packet distribution.png", bbox_inches="tight")
plt.clf()
