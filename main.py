import net_systems
import net_components
from libs.esper import esper
import zmq
import sys
import argparse
import time
from zmq.asyncio import Context, ZMQEventLoop
import asyncio

Url = 'tcp://127.0.0.1:5555'
Ctx = Context()


@asyncio.coroutine
def server():
    print("Getting ready for hello world client.  Ctrl-C to exit.\n")
    socket = Ctx.socket(zmq.REP)
    socket.bind(Url)
    while True:
        #  Wait for next request from client
        message = yield from socket.recv()
        print("Received request: {}".format(message))
        #  Do some "work"
        yield from asyncio.sleep(1)
        #  Send reply back to client
        message = message.decode('utf-8')
        message = '{}, world'.format(message)
        message = message.encode('utf-8')
        print("Sending reply: {}".format(message))
        yield from socket.send(message)


# TODO:  Implement a manager class for each aspect (ex: Network_Manager)
# TODO: Is it right to implement server-client as ESC ?...
def main():
    args = sys.argv[1:]
    if len(args) != 0:
        sys.exit(__doc__)
    try:
        loop =  asyncio.get_event_loop() 
        loop.run_until_complete(server())
    except KeyboardInterrupt:
        print('\nFinished (interrupted)')
        sys.exit(0)

    #  Socket to talk to server
    print("Connecting to hello world server...")
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")

    #  Do 10 requests, waiting each time for a response
    for request in range(10):
        print("Sending request %s ..." % request)
        socket.send(b"Hello")

        #  Get the reply.
        message = socket.recv()
        print("Received reply %s [ %s ]" % (request, message))


if __name__ == '__main__':
    main()
