import collections
import logging
import threading
from uuid import uuid4
import binascii
import os
from random import randint
import time
from enum import Enum

from libs import umsgpack, zmq
from net_components import RCFMessage
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

CONNECT_TIMEOUT = 2
WAITING_TIME = 0.001
SERVER_MAX = 1


