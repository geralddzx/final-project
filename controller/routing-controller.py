from p4utils.utils.topology import Topology
from p4utils.utils.sswitch_API import SimpleSwitchAPI
import draw_topology

class RoutingController(object):

    def __init__(self):

        self.topo = Topology(db="topology.db")

    def init(self):
        draw_topology.run(self.topo)

if __name__ == "__main__":
    controller = RoutingController()
