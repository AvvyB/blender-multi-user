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
    frame 3: body (blob) // Could be any data 

    """
    key = None  # key (string)
    id = None  # User  (string)
    body = None  # data blob


    def __init__(self,  key=None, id=None,  body=None):
        self.key = key
        self.body = body
        self.id = id

    def apply(self):
        pass

    def store(self, dikt, override=False):
        """Store me in a dict if I have anything to store"""
        # this currently erasing old value
        if self in dikt:
            if override:
                dikt[self.key] = self
        else:
            if self.key is not None:
                dikt[self.key] = self
        # elif self.key in dikt:
        #     del dikt[self.key]

    def send(self, socket):
        """Send key-value message to socket; any empty frames are sent as such."""
        key = ''.encode() if self.key is None else self.key.encode()
        body = ''.encode() if self.body is None else umsgpack.packb(self.body)
        id = ''.encode() if self.id is None else self.id

        try:
            socket.send_multipart([key, id, body])
        except:
            print("Fail to send {} {}".format(key, id))

    @classmethod
    def recv(cls, socket):
        """Reads key-value message from socket, returns new kvmsg instance."""
        key, id,  body = socket.recv_multipart(zmq.NOBLOCK)
        key = key.decode() if key else None
        id = id if id else None
        body = umsgpack.unpackb(body) if body else None

        return cls(key=key, id=id, body=body)

    def dump(self):
        if self.body is None:
            size = 0
            data = 'NULL'
        else:
            size = len(self.body)
            data = repr(self.body)
        print("[key:{key}][size:{size}] {data}".format(
            key=self.key,
            size=size,
            data=data,
        ))

