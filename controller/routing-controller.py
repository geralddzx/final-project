from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
import save_topology

class RoutingController(object):

    def __init__(self):
        self.topo = Topology(db="topology.db")

    def main(self):
        # save topology in files
        save_topology.main(self.topo)

if __name__ == "__main__":
    controller = RoutingController().main()
