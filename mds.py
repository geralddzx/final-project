import csv
import pdb
import random
import math
import matplotlib.pyplot as plt

points = None
paths = []
x = []
y = []
alpha = 0.1

def make_plot():
    plt.clf()
    plt.scatter(x, y)
    for i in range(len(points)):
        plt.annotate(points[i], (x[i], y[i]))
    plt.show()
    # plt.show(block=False)
    # plt.pause(0.01)
    # plt.close()

def get_distance(pair):
    return math.sqrt(pair[0] ** 2 + pair[1] ** 2)

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

for n in range(1000):
    for i in range(len(points)):
        for j in range(len(points)):
            expected = paths[i][j]
            if expected:
                diff = (x[j] - x[i], y[j] - y[i])
                distance = get_distance(diff)
                delta = math.log(distance / expected)

                delta *= alpha

                x[i] += diff[0] * delta
                y[i] += diff[1] * delta

        # if random.random() < 0:
        #     x[i] += random.uniform(-1, 1) * alpha
        #     y[i] += random.uniform(-1, 1) * alpha
make_plot()
