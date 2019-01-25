import net_systems
import net_components
from libs.esper import esper
import zmq
import sys
import argparse
import time


# TODO:  Implement a manager class for each aspect (ex: Network_Manager)
# TODO: Is it right to implement server-client as ESC ?...
def main():
    # Argument parsing
    parser = argparse.ArgumentParser(
        description='Launch an instance of collaboration system')
    parser.add_argument('-r', choices=list(net_components.Role),
                        type=net_components.Role, help='role for the instance ')

    args = parser.parse_args()

    instance_role = args.r
    instance_context = zmq.Context()

    print("Starting a {} instance \n".format(instance_role))

    # Create a World instance to hold everything:
    world = esper.World()

    # Instantiate a Processor (or more), and add them to the world:
    network_system = net_systems.NetworkSystem()
    world.add_processor(network_system)

    # Instanciate a session entity
    session = world.create_entity()

    world.add_component(
        session, net_components.NetworkInterface(context=instance_context))
    world.add_component(
        session, net_components.User(role=instance_role))

    # A dummy main loop:
    try:
        while True:
            # Call world.process() to run all Processors.
            world.process()
            time.sleep(1)
    except KeyboardInterrupt:
        return


if __name__ == '__main__':
    main()
