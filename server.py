"""
Clone server Model One

"""
import time
import zmq


def main():
    # Prepare our context and publisher socket
    ctx = zmq.Context()

    # Update all clients
    publisher = ctx.socket(zmq.PUB)
    publisher.bind("tcp://*:5555")
    time.sleep(0.2)

    # Update receiver
    state_request = ctx.socket(zmq.ROUTER)
    state_request.bind("tcp://*:5556")
    
    # poller for socket aggregation
    poller = zmq.Poller()
    poller.register(state_request, zmq.POLLIN)

    
    while True:
        try:
            socks = dict(poller.poll(1))
        except KeyboardInterrupt:
            break
            
        if state_request in socks:
            msg = state_request.recv_multipart()
            print(msg[0].decode('ascii'))
            print(msg[1].decode())
            publisher.send(b'Server update')
            
        # publisher.send_string('test')
        # print('msg')
        # time.sleep(1)
if __name__ == '__main__':
    main()
