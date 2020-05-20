import pdb
import csv
import os

def main(topology):
    nodes = [] # switches and hosts in topology
    hosts = set() # hosts in topology
    interfaces = [] # interfaces of each node in topology in the same order as nodes

    for sw_name in topology.get_p4switches().keys():
        nodes.append(sw_name)
        for host in topology.get_hosts_connected_to(sw_name):
            if not host in hosts:
                nodes.append(host)
                hosts.add(host)

    with open("edges.csv", "w") as file:
        # write node names names
        writer = csv.writer(file)
        writer.writerow(nodes)

        # write interfaces of each node
        for node in nodes:
            neighbors = [] # immediate neighbors of node
            if not node in hosts: # if a switch
                for interface, neighbor in topology.get_interfaces_to_node(node).items():
                    # store interface name and neighbor name in neighbors
                    neighbors.append(interface.split("-")[1] + " " + neighbor)
            writer.writerow(neighbors)

    with open("paths.csv", "w") as file:
        writer = csv.writer(file)
        writer.writerow(nodes)
        for i in range(len(nodes)):
            # write short path lengths from each node to each other node
            path_lengths = []
            for j in range(len(nodes)):
                shortest_paths = topology.get_shortest_paths_between_nodes(nodes[i], nodes[j])
                path_lengths.append(len(shortest_paths[0]) - 1)
            writer.writerow(path_lengths)
