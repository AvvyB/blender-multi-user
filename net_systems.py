import time
import asyncio

import zmq
import zmq.asyncio

import net_components 
from libs.esper import esper


class SessionSystem(esper.Processor):
    """
    Handle Client-Server session managment
    """

    def __init__(self):
        super().__init__()
        # Initialize poll set
        

    # TODO: Use zmq_poll..
    def process(self):
        # This will iterate over every Entity that has BOTH of these components:
        for ent, (net_interface, user) in self.world.get_components(net_components.NetworkInterface,net_components.User):
            if user.role is net_components.Role.SERVER:
                print("Server loops")
                try:
                    message = net_interface.socket.recv()
                    print("test")
                except KeyboardInterrupt:
                    break                   

                print("test")

            if user.role is net_components.Role.CLIENT:
                 #  Send reply back to client
                socket.send(b"Hello")
    
    @asyncio.coroutine
    def recv_and_process():
        sock = ctx.socket(zmq.PULL)
        sock.bind(url)
        msg = yield from sock.recv_multipart() # waits for msg to be ready
        reply = yield from async_process(msg)
        yield from sock.send_multipart(reply)
