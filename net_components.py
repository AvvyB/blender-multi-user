import zmq

class Role(Enum):
    NONE = 1
    SERVER = 2
    CLIENT = 3

class Replication(Enum):
    NONE = 1
    REPLICATED = 2
    REPNOTIFY = 3

class User:
    def __init__(self, name="default", ip="localhost",role=Role.NONE):
        self.name = name
        self.role = role

class NetworkInterface:
     def __init__(self, host="localhost",context=None, socket_type=zmq.REP,protocol='tcp',port=5555):
        self.host = host
        self.context = context
        self.socket_type = socket_type
        self.socket = context.socket(socket_type)
        
        #TODO: Is this right to it here?
        self.socket.bind("{}://{}:{}" % (protocol,host,port))

class Property:
    def __init__(self, property=None, replication=Replication.NONE):
        self.property = property
        self.replication = replication

class Function:
    def __init__(self, function=None):
        self.function = function        

