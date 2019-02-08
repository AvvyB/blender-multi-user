import zmq
import asyncio
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)


class Session():
    def __init__(self, host='127.0.0.1', port=5555, is_hosting=False):
        self.host = host
        self.port = port

        # init zmq context
        self.context = zmq.Context()

        # init socket interface
        if is_hosting:
            self.socket = self.context.socket(zmq.REP)
            self.socket.bind("tcp://*:5555")
        else:
            self.socket = self.context.socket(zmq.REQ)
            self.socket.connect("tcp://127.0.0.1:5555")

        self.listen = asyncio.ensure_future(self.listen())
        self.msg = []

    def is_running(self):
        try:
            return not self.listen.done
        except:
            return False

    # TODO: Add a kill signal to destroy clients session
    # TODO: Add a join method
    # TODO: Add a create session method

    async def listen(self):
        logger.info("Listening on {}:{}".format(self.host, self.port))

        while True:
            # Ungly blender workaround to prevent blocking...
            await asyncio.sleep(0.016)
            try:
                message = self.socket.recv_multipart(zmq.NOBLOCK)
                self.msg.append(message)
                logger.info(message)
            except zmq.ZMQError:
                pass

    def send(self, msg):
        logger.info("Sending {} to {}:{} ".format(msg, self.host, self.port))

        self.socket.send(b"msg")

    def close(self):
        logger.info("Closing session")
        self.listen.cancel()

