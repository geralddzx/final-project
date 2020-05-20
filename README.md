Automated Topology Visualization in P4
--------------------------------------

The goal of this project is to allow students to visualize their topology in their p4 environment through the terminal. This projects uses ideas inspired from http://www.itginsight.com/Files/paper/AN%20ALGORITHM%20FOR%20DRAWING%20GENERAL%20UNDIRECTED%20GRAPHS(Kadama%20Kawai%20layout).pdf to organize the topology based on theoretical graph distance between nodes (ie. the length of the shortest path between nodes). The algorithm runs 2000 iterations on a 4-fattree topology in about 5 seconds.

This algorithm should work on any topology, here are some example runs on line, medium and fattree topologies:

![line topology](images/line.png "Line Topology")
