from uuid import uuid4

try:
    from .libs import umsgpack
    from .libs import zmq
except:
    # Server import
    from libs import umsgpack
    from libs import zmq


class RCFMessage(object):
    """
    Message is formatted on wire as 2 frames:
    frame 0: key (0MQ string) // property path
    frame 1: id (0MQ string) // property path
    frame 2: mtype (0MQ string) // property path
    frame 3: body (blob) // Could be any data 

    """
    key = None  # key (string)
    id = None  # User  (string)
    mtype = None  # data mtype (string)
    body = None  # data blob
    uuid = None

    def __init__(self,  key=None, uuid=None, id=None, mtype=None, body=None):
        if uuid is None:
            uuid = uuid4().bytes

        self.key = key
        self.uuid = uuid
        self.mtype = mtype
        self.body = body
        self.id = id

    def apply(self):
        pass

    def store(self, dikt):
        """Store me in a dict if I have anything to store"""
        # this currently erasing old value
        if self.key is not None:
            dikt[self.key] = self
        # elif self.key in dikt:
        #     del dikt[self.key]

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = ''.encode() if self.key is None else self.key.encode()
        mtype = ''.encode() if self.mtype is None else self.mtype.encode()
        body = ''.encode() if self.body is None else umsgpack.packb(self.body)
        id = ''.encode() if self.id is None else self.id

        try:
            socket.send_multipart([key, id, mtype, body])
        except:
            logger.info("Fail to send {} {}".format(key, id))

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, id, mtype, body = socket.recv_multipart(zmq.DONTWAIT)
        key = key.decode() if key else None
        id = id if id else None
        mtype = mtype.decode() if body else None
        body = umsgpack.unpackb(body) if body else None

        return cls(key=key, id=id, mtype=mtype, body=body)

    def dump(self):
        if self.body is None:
            size = 0
            data = 'NULL'
        else:
            size = len(self.body)
            data = repr(self.body)
        print("[key:{key}][size:{size}][mtype:{mtype}] {data}".format(
            key=self.key,
            size=size,
            mtype=self.mtype,
            data=data,
        ))

