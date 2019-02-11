

"""
Clone Client Model One

Author: Min RK <benjaminrk@gmail.com>

"""

import random
import time
import msgpack
import zmq

from libs import kvsimple

def main():
    # Prepare our context and publisher socket
    ctx = zmq.Context()

    # Update socket binding
    updates = ctx.socket(zmq.SUB)
    updates.linger = 0
    updates.connect("tcp://localhost:5555")
    updates.setsockopt_string(zmq.SUBSCRIBE, '')

    state_request = ctx.socket(zmq.DEALER)
    state_request.setsockopt(zmq.IDENTITY, b"PEER2")
    state_request.linger = 0
    state_request.connect("tcp://localhost:5556")
    
    # poller for socket aggregation
    poller = zmq.Poller()
    poller.register(updates, zmq.POLLIN)

    while True:  
        try:
            socks = dict(poller.poll(10))
        except KeyboardInterrupt:
            break

        if updates in socks:
            message = updates.recv_multipart()
            print(message)
        
        # Send update

        new_state= b"test"
        state_request.send(new_state)
        print("Sending {}".format(new_state))
        time.sleep(1)
        
    
   
        
if __name__ == '__main__':
    main()


