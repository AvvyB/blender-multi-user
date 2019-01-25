import time

import zmq

import net_components 
from libs.esper import esper


class NetworkSystem(esper.Processor):
    """
    Handle Client-Server session managment
    """

    def __init__(self):
        super().__init__()


    def process(self):
        # This will iterate over every Entity that has BOTH of these components:
        for ent, (net_interface, user) in self.world.get_components(net_components.NetworkInterface,net_components.User):
            if user.role is net_components.Role.CLIENT:
                net_interface.socket.send(b"Waiting server response")

            if user.role is net_components.Role.SERVER:
                net_interface.socket.recv(b"Waiting server response")
