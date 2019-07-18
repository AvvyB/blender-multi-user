import unittest
from replication import ReplicatedDatablock, ReplicatedDataFactory
import umsgpack
import logging
from replication_client import Client, Server
import time


log = logging.getLogger(__name__)

class SampleData():
    def __init__(self):
        self.map = {
            "sample":"data",
            "sample":"data",
            "sample":"data",
            "sample":"data"
            }

class RepSampleData(ReplicatedDatablock):
    def serialize(self,data):
        import pickle

        return pickle.dumps(data)

    def deserialize(self,data):
        import pickle

        return pickle.load(data)

class TestDataReplication(unittest.TestCase):

    def test_setup_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)
        data_sample = SampleData()
        rep_sample = factory.construct_from_dcc(data_sample)(owner="toto")
        
        self.assertEqual(isinstance(rep_sample,RepSampleData), True)

    def test_replicate_client_data(self):        
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server_api = Server(factory=factory)
        server_api.serve()
        client_api = Client(factory=factory)
        client_api.connect()

        data_sample = SampleData()
        data_sample_key = client_api.register(data_sample)

        #Waiting for server to receive the datas
        time.sleep(.1)

        #Check if if receive them
        self.assertNotEqual(server_api._rep_store[data_sample_key],None)

    



if __name__ == '__main__':
    unittest.main()