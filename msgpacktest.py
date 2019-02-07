import time
import zmq
import asyncio

print('asyncio test')

context = zmq.Context()

async def server(ctx):
    print("Launching server...") 
        
    socket = ctx.socket(zmq.REP)
    socket.bind("tcp://*:5555")
    
    while True:
        #print('start loop')
        await asyncio.sleep(0.016)
        try:
            # this is currenlty necessary to ensure no dropped monitor messages
            # see LIBZMQ-248 for more info
            message = socket.recv_multipart()
            print("Received request: {}".format(message))
            
            socket.send(b"Hello from server")
        except zmq.ZMQError:
            pass
        
        
async def client(ctx):
    print("Launching client...")  
    
    socket = ctx.socket(zmq.REQ)
    socket.connect("tcp://localhost:5555")
    
    await asyncio.sleep(1)
    
    #  Do 10 requests, waiting each time for a response
    for request in range(10):
        print("Sending request %s ..." % request)
        socket.send(b"Hello from cli")
        
        await asyncio.sleep(.016)
        #  Get the reply.
        try:
            message = socket.recv_multipart(zmq.NOBLOCK)
            print("Received reply %s [ %s ]" % (request, message))
        except zmq.ZMQError:
            pass


print("setup server")  
asyncio.create_task(server(context))

time.sleep(1)

print("setup client")  
asyncio.create_task(client(context))
