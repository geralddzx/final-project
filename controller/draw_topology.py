import csv
import pdb
import random
import math
from curses import wrapper
import curses
import numpy as np
import sys

def get_distance(pair):
    return math.sqrt(pair[0] ** 2 + pair[1] ** 2)

nodes = None # nodes in the topology
# length of shortest path of each node to each other node
# use to determine theoretical distance between nodes
path_lengths = []
x = []
y = []
alpha = 0.002 # learning rate
neighbors = [] # neighbors of each node
interfaces = [] # interfaces of each node corresponding to each neighbor in neighbors
num_iterations = 2500
num_edges = 0 # edge count, this is used to determine whether to show the interfaces in the drawing

# load eges from file
with open("edges.csv", "r") as file:
    reader = csv.reader(file)
    nodes = next(reader)
    for row in reader:
        # give node random location initially
        x.append(random.uniform(0, 1))
        y.append(random.uniform(0, 1))

        node_neighbors = []
        node_interfaces = []
        for interface in row:
            port, node = interface.split(" ")
            node_neighbors.append(node)
            node_interfaces.append(port)
            num_edges += 1
        neighbors.append(node_neighbors)
        interfaces.append(node_interfaces)

# load path lengths from file
with open("paths.csv", "r") as file:
    reader = csv.reader(file)
    nodes = next(reader)
    for row in reader:
        lengths = []
        for i in row:
            lengths.append(int(i))
        path_lengths.append(lengths)

# renders the current state of the topology based on the location of each node
def render(stdscr):
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)

    stdscr.clear()
    min_x = np.array(x).min()
    min_y = np.array(y).min()
    width = (np.array(x).max() - min_x) * 1.05
    height = (np.array(y).max() - min_y) * 1.05

    # only draw interface if nodes and edges are sparse
    draw_eth = 2 * num_edges + len(nodes) < 0.01 * curses.LINES * curses.COLS


    tile_x = []
    tile_y = []
    # convert to tile coordinates
    for i in range(len(x)):
        tile_x.append((x[i] - min_x) / width * curses.COLS)
        tile_y.append((y[i] - min_y) / height * curses.LINES)

    for i in range(len(tile_x)):
        # print sw_name
        stdscr.addstr(int(tile_y[i]), int(tile_x[i]), nodes[i], curses.A_BOLD | curses.color_pair(1))

        for neighbor in range(len(neighbors[i])):
            j = nodes.index(neighbors[i][neighbor]) # node index of neighbor

            diff = (tile_x[j] - tile_x[i], tile_y[j] - tile_y[i]) # vector pointing to neighbor
            if diff[0] and diff[1]:
                # adjusted distance based on the fact that tiles are 2:1 height:width aspect ratio
                distance = math.sqrt(diff[0] ** 2 + (diff[1] * 2) ** 2)

                step = 1 # draw a dot between node and its neighbor every step
                while step < distance:
                    p = step / distance # p is percent of distance covered at current step
                    (point_x, point_y) = (tile_x[i] + diff[0] * p, tile_y[i] + diff[1] * p)

                    # draw interface info at step 20
                    if draw_eth and step == 10:
                        stdscr.addstr(int(point_y), int(point_x), interfaces[i][neighbor], curses.color_pair(2))

                    # draw a dot at every 5 steps to show connection
                    if step % 5 == 0:
                        if stdscr.inch(int(point_y), int(point_x)) == 32: # if space not taken by node or interface name
                            stdscr.addch(int(point_y), int(point_x), ".")
                    step += 1
    stdscr.addstr(0, 0, "Here's your topology, press any key to continue...")
    stdscr.refresh()


# make drawing better by bringing nodes closer to theoretical graph distance between each other
# http://www.itginsight.com/Files/paper/AN%20ALGORITHM%20FOR%20DRAWING%20GENERAL%20UNDIRECTED%20GRAPHS(Kadama%20Kawai%20layout).pdf
def train(stdscr, should_render):
    iter = 0
    while iter < num_iterations:
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                # theoretical distance between node i and node j
                expected_distance = path_lengths[i][j]
                if expected_distance:
                    diff = (x[j] - x[i], y[j] - y[i])
                    distance = get_distance(diff) # actual distance of current state of topology
                    if iter / num_iterations < 0.5: # the first half of training
                        delta = math.log(distance / expected_distance) # focus on bringing distance / expected_distance to 1
                    else:
                        delta = -(expected_distance / distance) ** (iter / num_iterations + 0.5) + 1 # focus on spreading nodes that are too close
                    delta *= alpha # scale by learning rate

                    # update position by improving distance between node i and node j
                    x[i] += diff[0] * delta
                    y[i] += diff[1] * delta
        iter += 1
        if should_render:
            render(stdscr) # render current state

    render(stdscr)
    stdscr.getch()

print("training model...if you want to see training process, run python3 controller/draw_topology.py true")
wrapper(train, len(sys.argv) > 1)
