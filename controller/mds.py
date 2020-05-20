import csv
import pdb
import random
import math
from curses import wrapper
import curses
import numpy as np

def get_distance(pair):
    return math.sqrt(pair[0] ** 2 + pair[1] ** 2)

nodes = None
paths = []
x = []
y = []
alpha = 0.02
neighbors = []
interfaces = []
num_iterations = 500
edges = 0

with open("edges.csv", "r") as file:
    reader = csv.reader(file)
    nodes = next(reader)
    for row in reader:
        node_neighbors = []
        node_interfaces = []
        for interface in row:
            port, node = interface.split(" ")
            node_neighbors.append(node)
            node_interfaces.append(port)
            edges += 1
        neighbors.append(node_neighbors)
        interfaces.append(node_interfaces)

with open("paths.csv", "r") as file:
    reader = csv.reader(file)
    nodes = next(reader)
    for row in reader:
        distances = []
        for i in row:
            distances.append(int(i))
        paths.append(distances)
        x.append(random.uniform(-1, 1))
        y.append(random.uniform(-1, 1))

def train():
    for num in range(num_iterations):
        for i in range(len(nodes)):
            for j in range(len(nodes)):
                expected = paths[i][j]
                if expected:
                    diff = (x[j] - x[i], y[j] - y[i])
                    distance = get_distance(diff)
                    if num / num_iterations < 0.5:
                        delta = math.log(distance / expected)
                    else:
                        delta = -(expected / distance) + 1
                    delta *= alpha

                    x[i] += diff[0] * delta
                    y[i] += diff[1] * delta
train()

def render(min_x, min_y, width, height, draw_eth,stdscr):
    for i in range(len(x)):
        x[i] = (x[i] - min_x) / width * curses.COLS
        y[i] = (y[i] - min_y) / height * curses.LINES

    for i in range(len(x)):
        stdscr.addstr(int(y[i]), int(x[i]), nodes[i], curses.A_BOLD | curses.color_pair(1))

        for k in range(len(neighbors[i])):
            j = nodes.index(neighbors[i][k])

            diff = (x[j]- x[i], y[j] - y[i])
            if diff[0] and diff[1]:
                distance = math.sqrt(diff[0] ** 2 + (diff[1] * 2.2) ** 2)

                step = 0
                while step < distance:
                    p = step / distance
                    (point_x, point_y) = (x[i] + diff[0] * p, y[i] + diff[1] * p)

                    if step == 20 and draw_eth:
                        if stdscr.inch(int(point_y), int(point_x)) == 32:
                            stdscr.addstr(int(point_y), int(point_x), interfaces[i][k], curses.color_pair(2))

                    if step % 10 == 0:
                        if stdscr.inch(int(point_y), int(point_x)) == 32:
                            stdscr.addch(int(point_y), int(point_x), ".")
                    step += 1
    stdscr.addstr(0, 0, "Here's your topology, press any key to continue...")

def draw(stdscr):
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    min_x = np.array(x).min()
    min_y = np.array(y).min()
    width = (np.array(x).max() - min_x) * 1.05
    height = (np.array(y).max() - min_y) * 1.05
    draw_eth = edges + len(nodes) < 0.01 * curses.LINES * curses.COLS
    render(min_x, min_y, width, height, draw_eth, stdscr)


    stdscr.refresh()
    stdscr.getch()


wrapper(draw)
