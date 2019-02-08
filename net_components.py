import zmq
import asyncio
import logging
from .libs import umsgpack

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
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect("tcp://localhost:5555")
            self.listen = asyncio.ensure_future(self.listen())
            return True

        except zmq.ZMQError:
            logger.error("Error while joining  {}:{}".format(
                self.host, self.port))

        return False

    # TODO: Find better names
    def create(self):
        logger.info("Creating session")
        try:
            self.socket = self.context.socket(zmq.REP)
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
                msg = self.socket.recv(zmq.NOBLOCK)
                # self.msg.append(umsgpack.unpackb(message))
                print(msg)
                logger.info(msg)
            except zmq.ZMQError:
                pass

    def send(self, msg):
        logger.info("Sending {} to {}:{} ".format(msg, self.host, self.port))
        bin = umsgpack.packb(msg)
        self.socket.send(bin,zmq.NOBLOCK)

    async def close_success(self):
        self.is_running = False

    def close(self):
        logger.info("Closing session")
        self.socket.close()
        self.listen.cancel()
        del self.listen
        self.is_running = False
