import net_systems
from libs.esper import esper
import zmq
import sys
import time

# TODO:  Implement a manager class for each aspect (ex: Network_Manager)
# TODO: Is it right to implement server-client as ESC ?...
def main(argv):
    # Create a World instance to hold everything:
    world = esper.World()

    # Instantiate a Processor (or more), and add them to the world:
    network_system = net_systems.NetworkSystem()
    world.add_processor(network_system)

    # A dummy main loop:
    try:
        while True:
            # Call world.process() to run all Processors.
            world.process()
            time.sleep(1)

    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main(sys.argv[1:])
    
