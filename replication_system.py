import zmq

from libs.esper import esper

class ReplicationSystem(esper.Processor):
    """
    Handle Client-Server session managment
    """

    def __init__(self):
        super().__init__()
        # Initialize poll set
        

    # TODO: Use zmq_poll..
    async def process(self):
        # This will iterate over every Entity that has BOTH of these components:
        print("test")