import pdb
import csv
import os

def run(topology):
    nodes = []
    hosts = set()
    interfaces = []

    for sw_name in topology.get_p4switches().keys():
        nodes.append(sw_name)
        for host in topology.get_hosts_connected_to(sw_name):
            if not host in hosts:
                nodes.append(host)
                hosts.add(host)

    with open("edges.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(nodes)
        for node in nodes:
            neighbors = []
            if not node in hosts:
                for interface, neighbor in topology.get_interfaces_to_node(node).items():
                    neighbors.append(interface + " " + neighbor)
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
