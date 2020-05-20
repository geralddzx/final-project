import pdb
import csv
import os

def run(topology):
    nodes = set()
    for sw_name in topology.get_p4switches().keys():
        nodes.add(sw_name)
        for host in topology.get_hosts_connected_to(sw_name):
            nodes.add(host)
    nodes = list(nodes)

    with open("edges.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(nodes)
        for node in nodes:
            neighbors = []
            for interface, neighbor in topology.get_interfaces_to_node(node).items():
                port = topology.interface_to_port(node, interface)
                neighbors.append(str(port) + " " + neighbor)
            writer.writerow(neighbors)

    with open("paths.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(nodes)
        for i in range(len(nodes)):
            paths = []
            for j in range(len(nodes)):
                shortest_paths = topology.get_shortest_paths_between_nodes(nodes[i], nodes[j])
                paths.append(len(shortest_paths[0]) - 1)
            writer.writerow(paths)
