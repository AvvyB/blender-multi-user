import bpy
from .libs.replication.constants import *
from . import operators

class Timer():
    def __init__(self, duration=1):
        self._timeout = duration

    def start(self):
        bpy.app.timers.register(self.execute)

    def execute(self):
        return self._timeout

    def stop(self):
        bpy.app.timers.unregister(self.execute)

class ApplyTimer(Timer):
    def __init__(self, timout=1,target_type=None):
        self._type = target_type
        super().__init__(timout)

    def execute(self):
        if operators.client:
            nodes = operators.client.list(filter=self._type)

            for node in nodes:
                node_ref = operators.client.get(node)

                if node_ref.state == FETCHED:
                    operators.client.apply(uuid=node)

        return self._timeout