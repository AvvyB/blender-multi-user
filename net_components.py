import zmq
import asyncio
import logging
from .libs import umsgpack
from .libs import kvsimple
import time
import random


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Session():
    def __init__(self, host='127.0.0.1', port=5555, is_hosting=False):
        self.host = host
        self.port = port
        self.is_running = False
        # init zmq context
        self.context = zmq.Context()
        self.socket = None
        
        self.msg = []
       
        #self.listen.add_done_callback(self.close_success())

    # TODO: Add a kill signal to destroy clients session
    # TODO: Add a join method
    # TODO: Add a create session method
    def join(self):
        logger.info("joinning  {}:{}".format(self.host, self.port))
        try:
            self.socket = self.context.socket(zmq.DEALER)
            self.socket.connect("tcp://localhost:5555")
            self.listen = asyncio.ensure_future(self.listen())
            
            self.send("XXX connected")
            return True

        except zmq.ZMQError:
            logger.error("Error while joining  {}:{}".format(
                self.host, self.port))

        return False

    # TODO: Find better names
    def create(self):
        logger.info("Creating session")
        try:
            self.socket = self.context.socket(zmq.ROUTER)
            self.socket.bind("tcp://*:5555")

            self.listen = asyncio.ensure_future(self.listen())
            return True
        except zmq.ZMQError:
            logger.error("Error while creating session: ",zmq.ZMQError)

        return False

    async def listen(self):
        logger.info("Listening on {}:{}".format(self.host, self.port))

        self.is_running = True
        while True:
            # Ungly blender workaround to prevent blocking...
            await asyncio.sleep(0.016)
            try:
                buffer = self.socket.recv(zmq.NOBLOCK)

                message = umsgpack.unpackb(buffer)
                if message is not 0:
                    self.socket.send(umsgpack.packb(0))
                    self.msg.append()
            except zmq.ZMQError:
                pass

    def send(self, msg):
        logger.info("Sending {} to {}:{} ".format(msg, self.host, self.port))
        self.msg.append(msg)
        bin = umsgpack.packb(msg)
        self.socket.send(bin)

    async def close_success(self):
        self.is_running = False

    def close(self):
        logger.info("Closing session")
        self.socket.close()
        self.listen.cancel()
        del self.listen
        self.is_running = False

class Client_poller():
    def __init__(self, id):
        
        self.id = id   
        self.listen = asyncio.ensure_future(self.listen())
        logger.info("client initiated {}".format(self.id))
    
    async def listen(self):
        context = zmq.Context()
        logger.info("...context  initiated {}".format(self.id))
        socket = context.socket(zmq.DEALER)
        identity = self.id
        socket.identity = identity.encode('ascii')
        logger.info("...socket  initiated {}".format(self.id))
        logger.info("client {} started".format(self.id))
        poll = zmq.Poller()
        poll.register(socket, zmq.POLLIN)

        await asyncio.sleep(1)

        while True:
            await asyncio.sleep(0.016)
            sockets = dict(poll.poll(1))
            
            if socket in sockets:
                msg = socket.recv(zmq.NOBLOCK)
                logger.info("{} received:{}".format(self.id, msg))


    def stop(self):
        logger.info("Stopping client {}".format(self.id))
        self.listen.cancel()

class Client():
    def __init__(self, context=None):
        
        if context is None:
            logger.info("client init default context")
            self.context = zmq.Context()
        else:
            self.context = context

        self.task = asyncio.ensure_future(self.run())
        logger.info("client initiated")
    
    async def run(self):
       # Prepare our context and publisher socket
        logger.info("configuring:")
        updates = self.context.socket(zmq.SUB)
        logger.info("..socket")
        updates.linger = 0
        logger.info("..linger")
        updates.setsockopt(zmq.SUBSCRIBE,b"10001")
        logger.info("client launched")
        updates.connect("tcp://localhost:5556")

        kvmap = {}
        sequence = 0
        
        while True:
            await asyncio.sleep(0.016)
            try:
                kvmsg = kvsimple.KVMsg.recv(updates)
            except:
                break # Interrupted
            kvmsg.store(kvmap)
            sequence += 1


    def stop(self):
        logger.info("Stopping client")
        self.task.cancel()



    kvmap = {}
    sequence = 0

class Server():
    def __init__(self):
        self.context = zmq.Context()
        self.task = asyncio.ensure_future(self.run())
        logger.info("server initiated ")
    
    async def run(self):
        publisher = self.context.socket(zmq.PUB)

        publisher.bind("tcp://*:5556")
        time.sleep(0.2)
        logger.info("server launched")

        sequence = 0
        random.seed(time.time())
        kvmap = {}

        while True:
            # Non blocking
            await asyncio.sleep(0.016)

            # Distribute as key-value message
            sequence += 1
            kvmsg = kvsimple.KVMsg(sequence)
            kvmsg.key = "%d" % random.randint(1,10000)
            kvmsg.body = "%d" % random.randint(1,1000000)
            kvmsg.send(publisher)
            kvmsg.store(kvmap)
    

    def stop(self):
        logger.info("Stopping server")
        self.task.cancel()