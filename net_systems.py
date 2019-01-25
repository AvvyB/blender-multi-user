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
        for ent, session in self.world.get_component(net_components.Session):

            #  Wait for next request from client
            message = session.socket.recv()
            print("Received request: %s" % message)

            #  Do some 'work'
            time.sleep(1)

            #  Send reply back to client
            session.socket.send(b"World")
