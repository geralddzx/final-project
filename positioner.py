import csv
import pdb
import random
import math
import matplotlib.pyplot as plt

alpha = 0.01
points = dict()

def make_plot():
    plt.clf()
    x = []
    y = []
    labels = []
    for point, point_data in points.items():
        labels.append(point)
        x.append(point_data[0])
        y.append(point_data[1])

    plt.scatter(x, y)

    for i in range(len(x)):
        plt.annotate(labels[i], (x[i], y[i]))
    plt.show()

def compute_score():
    loss = 0
    for point, point_data in points.items():
        for target, target_data in points.items():
            if target in point_data[2]:
                distance = (point_data[0] - target_data[0]) ** 2 + (point_data[1] - target_data[1]) ** 2
                loss += distance
    return loss


with open("topology.csv", "r") as file:
    reader = csv.reader(file)
    for row in reader:
        points[row[0]] = [random.uniform(0, 1), random.uniform(0, 1), set(row[1:])]

for i in range(10000):
    for point, point_data in points.items():
        for target, target_data in points.items():
            if target != point:
                # if random.random() < 0.1:
                #     old_score = compute_score()
                #     x, y = point_data[0], point_data[1]
                #     point_data[0] = target_data[0]
                #     point_data[1] = target_data[1]
                #     target_data[0] = x
                #     target_data[1] = y
                #     if old_score > compute_score():
                #         target_data[0] = point_data[0]
                #         target_data[1] = point_data[1]
                #         point_data[0] = x
                #         point_data[1] = y


                diff = (target_data[0] - point_data[0], target_data[1] - point_data[1])
                mag = diff[0] ** 2 + diff[1] ** 2
                if mag:
                    #
                    # if mag:
                    #     if not target in point_data[2]:
                    #         scale = -math.sqrt(mag) / mag
                    #     else:
                    #         scale = mag ** 2 / mag
                    #     beta = alpha * scale

                    beta = -1 / mag

                    if target in point_data[2]:
                        beta += math.exp(mag) * 10

                    beta = beta * alpha

                    new_x = diff[0] * beta + point_data[0]
                    point_data[0] = max(min(new_x, 1), 0)
                    new_y = diff[1] * beta + point_data[1]
                    point_data[1] = max(min(new_y, 1), 0)

                point_data[0] += random.uniform(-alpha * 2, alpha * 2)
                point_data[1] += random.uniform(-alpha * 2, alpha * 2)

                center_diff = (0.5 - point_data[0], 0.5 - point_data[1])
                scale = (len(point_data[2]) / len(points)) ** 2
                point_data[0] += center_diff[0] * scale
                point_data[1] += center_diff[1] * scale

                alpha *= 0.99999999

    if i % 1000 == 0:
        make_plot()
