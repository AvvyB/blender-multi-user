import zmq
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
     def __init__(self, host="127.0.0.1",context=None, socket_type=zmq.REP,protocol='tcp',port=5555):
        self.host = host
        self.context = context
        self.socket = context.socket(socket_type)
        
        #TODO: Is this right to it here?
        self.socket.bind("{}://{}:{}".format(protocol,host,port))

class Property:
    def __init__(self, property=None, replication=Replication.NONE):
        self.property = property
        self.replication = replication

class Function:
    def __init__(self, function=None):
        self.function = function        

