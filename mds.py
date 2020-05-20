import csv
import pdb
import random
import math
import matplotlib.pyplot as plt
from curses import wrapper
import curses
import numpy as np
import time

points = None
paths = []
x = []
y = []
alpha = 0.02
beta = 0.0001
connections = []
interfaces = []
num_iterations = 300

def make_plot():
    plt.clf()
    plt.scatter(x, y)
    for i in range(len(points)):
        plt.annotate(points[i], (x[i], y[i]))
    # plt.show()
    plt.show(block=False)
    plt.pause(0.01)
    plt.close()

def get_distance(pair):
    return math.sqrt(pair[0] ** 2 + pair[1] ** 2)

with open("topology.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        conn = []
        inter = []
        for connection in row[1:]:
            interface, node = connection.split(" ")
            conn.append(node)
            inter.append(interface)
        connections.append(conn)
        interfaces.append(inter)

with open("paths.csv", "r") as file:
    reader = csv.reader(file)
    points = next(reader)
    for row in reader:
        distances = []
        for i in row:
            distances.append(int(i))
        paths.append(distances)
        x.append(random.uniform(-1, 1))
        y.append(random.uniform(-1, 1))

for num in range(num_iterations):
    for i in range(len(points)):
        for j in range(len(points)):
            expected = paths[i][j]
            if expected:
                diff = (x[j] - x[i], y[j] - y[i])
                distance = get_distance(diff)
                if num / num_iterations < 0.5:
                    delta = math.log(distance / expected)
                else:
                    delta = -(expected / distance) + 1
                # delta = delta * (1 / distance) ** beta

                delta *= alpha

                x[i] += diff[0] * delta
                y[i] += diff[1] * delta
    beta = beta * 1.1
    make_plot()

def draw(stdscr):
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    min_x = np.array(x).min()
    min_y = np.array(y).min()
    width = np.array(x).max() - min_x
    width *= 1.05
    tile_width = width / curses.COLS
    height = np.array(y).max() - min_y
    tile_height = height / curses.LINES
    height *= 1.05
    pad = curses.newpad(curses.LINES, curses.COLS)

    for i in range(len(x)):
        x_coord = (x[i] - min_x) / width * curses.COLS
        y_coord = (y[i] - min_y) / height * curses.LINES

        for k in range(len(connections[i])):
            j = points.index(connections[i][k])
            x1 = int((x[j] - min_x) / width * curses.COLS)
            y1 = int((y[j] - min_y) / height * curses.LINES)

            diff = (x[j]- x[i], y[j] - y[i])
            if diff[0] and diff[1]:
                step_size = min(abs(tile_width / diff[0]) * 4, abs(tile_height / diff[1]) * 4)

                cur = step_size
                count = 0
                while cur < 1:

                    (point_x, point_y) = (x[i] + diff[0] * cur, y[i] + diff[1] * cur)
                    tile_x, tile_y = ((point_x - min_x) / width * curses.COLS, (point_y - min_y) / height * curses.LINES)

                    if False:
                        pad.addstr(int(tile_y), int(tile_x), interfaces[i][k].split("-")[1], curses.A_DIM | curses.color_pair(2))
                    else:
                        if pad.inch(int(tile_y), int(tile_x)) == 32:
                            pad.addch(int(tile_y), int(tile_x), ".")
                    cur += step_size
                    count += 1


        pad.addstr(int(y_coord), int(x_coord), points[i], curses.A_BOLD | curses.color_pair(1))





    # stdscr.clear()
    # stdscr.addstr(0, 0, "o")
    # stdscr.refresh()

    pad.refresh(0, 0, 0, 0, curses.LINES, curses.COLS)
    #
    input("")

wrapper(draw)
