import logging
import uuid
try:
    from .libs import umsgpack

except:
    # Server import
    from libs import umsgpack

import zmq

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class Data(object):
    """
    Datablock used for replication 

    """
    uuid = None  # key (string)
    owner = None  # User  (string)
    data = None  # data blob

    def __init__(self,  uuid=None, owner=None,  data=None):
        self.key = str(uuid.uuid4())
        self.data = data
        self.id = id

    

