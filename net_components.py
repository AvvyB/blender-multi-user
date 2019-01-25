
class User:
    def __init__(self, name="default", ip="localhost"):
        self.name = name
        self.ip = ip

class Session:
     def __init__(self, name="default", host="localhost"):
        self.name = name
        self.host = host

class Position:
    def __init__(self, x=0, y=0,z=0):
        self.x = x
        self.y = y
        self.z = z

class Property:
    def __init__(self, property=None):
        self.property = property

class Function:
    def __init__(self, function=None):
        self.function = function        