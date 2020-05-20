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

with open("edges.csv", "r") as file:
    reader = csv.reader(file)
    points = next(reader)
    for row in reader:
        conn = []
        inter = []
        for connection in row:
            port, node = connection.split(" ")
            conn.append(node)
            inter.append(port)
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
    # make_plot()

def draw(stdscr):
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)
    min_x = np.array(x).min()
    min_y = np.array(y).min()
    width = (np.array(x).max() - min_x) * 1.05
    height = (np.array(y).max() - min_y) * 1.05

    for i in range(len(x)):
        x[i] = (x[i] - min_x) / width * curses.COLS
        y[i] = (y[i] - min_y) / height * curses.LINES

    for i in range(len(x)):
        stdscr.addstr(int(y[i]), int(x[i]), points[i], curses.A_BOLD | curses.color_pair(1))

        for k in range(len(connections[i])):
            j = points.index(connections[i][k])
            x1 = int(x[j])
            y1 = int(y[j])

            diff = (x[j]- x[i], y[j] - y[i])
            if diff[0] and diff[1]:
                distance = math.sqrt(diff[0] ** 2 + (diff[1] * 2.2) ** 2)

                step = 0
                while step < distance:
                    p = step / distance
                    (point_x, point_y) = (x[i] + diff[0] * p, y[i] + diff[1] * p)

                    if step == 10:
                        stdscr.addstr(int(point_y), int(point_x), interfaces[i][k], curses.color_pair(2))
                    elif step % 7 == 0:
                        if stdscr.inch(int(point_y), int(point_x)) == 32:
                            stdscr.addch(int(point_y), int(point_x), ".")
                    step += 1
        stdscr.addstr(int(y[i]), int(x[i]), points[i], curses.A_BOLD | curses.color_pair(1))
    stdscr.addstr(0, 0, "Here's your topology, press any key to continue...")


    # stdscr.clear()
    # stdscr.addstr(0, 0, "o")
    # stdscr.refresh()
    stdscr.refresh()
    stdscr.getch()
    #


wrapper(draw)
