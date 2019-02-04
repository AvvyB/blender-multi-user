import zmq
# from zmq.asyncio import Context, ZMQEventLoop
# import asyncio
from enum import Enum, auto

class Role(Enum):
    NONE = 'NONE'
    SERVER = 'SERVER'
    CLIENT = 'CLIENT'

    def __str__(self):
        return self.value

class Replication(Enum):
    NONE = auto()
    REPLICATED = auto()
    REPNOTIFY = auto()

class User:
    def __init__(self, name="default", ip="localhost",role=Role.NONE):
        self.name = name
        self.role = role

class NetworkInterface:
     def __init__(self, host="*",context=None, socket_type=zmq.REQ,protocol='tcp',port=5555):
        self.host = host
        self.context = context
        self.socket = context.socket(socket_type)
        self.poller = zmq.Poller()
       
        #TODO: Is this right to it here?
        self.poller.register(self.socket, zmq.POLLIN)
        print("{}://{}:{}".format(protocol,host,port))
        self.socket.bind("tcp://*:5555")

class Property:
    def __init__(self, property=None, replication=Replication.NONE):
        self.property = property
        self.replication = replication

class Function:
    def __init__(self, function=None):
        self.function = function        


