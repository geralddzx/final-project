import csv
import pdb
import random
import math
import matplotlib.pyplot as plt

points = []
x = []
y = []
connections = []
alpha = 0.002

def make_plot():
    plt.clf()
    plt.scatter(x, y)
    for i in range(len(points)):
        plt.annotate(points[i], (x[i], y[i]))
    plt.show()

def compute_score():
    loss = 0
    for i in range(len(points)):
        for j in range(len(points)):
            if points[j] in connections[i]:
                loss += get_distance(x[i] - x[j], y[i] - y[j]) ** 2
    return -loss

def get_distance(x, y):
    return max(0.00000001, x ** 2 + y ** 2)

def bound(x):
    return max(min(x, 1), 0)

with open("topology.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        points.append(row[0])
        x.append(random.uniform(0, 1))
        y.append(random.uniform(0, 1))
        connections.append(set(row[1:]))

for n in range(10000):
    for i in range(len(points)):
        for j in range(len(points)):
            if random.random() < 0.01:
                old_score = compute_score()
                x0, y0 = x[i], y[i]
                x[i], y[i] = x[j], y[j]
                x[j], y[j] = x0, y0
                if old_score > compute_score():
                    x[j], y[j] = x[i], y[i]
                    x[i], y[i] = x0, y0

            diff = (x[j] - x[i], y[j] - y[i])
            distance = get_distance(diff[0], diff[1])
            scale = -alpha / distance
            x[i] = bound(x[i] + scale * diff[0])
            y[i] = bound(y[i] + scale * diff[1])

            if points[j] in connections[i]:
                scale = distance ** 4 * alpha
                x[i] = x[i] + scale * diff[0]
                y[i] = y[i] + scale * diff[1]
            #     else:
            #         scale = mag ** 2 / mag
            #     beta = alpha * scale

        diff = (0.5 - x[i], 0.5 - y[i])
        scale = alpha * len(connections[i]) ** 2
        x[i] += diff[0] * scale
        y[i] += diff[1] * scale

                    #
                    # if mag:
                    #     if not target in point_data[2]:
                    #         scale = -math.sqrt(mag) / mag
                    #     else:
                    #         scale = mag ** 2 / mag
                    #     beta = alpha * scale

                    # beta = -1 / mag

                    # if target in point_data[2]:
                    #     beta += math.exp(mag) * 10

                #
                # point_data[0] += random.uniform(-alpha * 2, alpha * 2)
                # point_data[1] += random.uniform(-alpha * 2, alpha * 2)



                # alpha *= 0.99999999

    if n % 100 == 0:
        make_plot()
