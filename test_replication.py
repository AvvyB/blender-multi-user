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

    def test_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)
        data_sample = SampleData()
        rep_sample = factory.construct_from_dcc(data_sample)(owner="toto")
        
        self.assertEqual(isinstance(rep_sample,RepSampleData), True)

    def test_basic_client_start(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        server.serve()

        client = Client(factory=factory)
        client.connect()

        time.sleep(1)

        self.assertEqual(client.state(), 2)

    # def test_register_client_data(self):
    #     # Setup data factory        
    #     factory = ReplicatedDataFactory()
    #     factory.register_type(SampleData, RepSampleData)

    #     server = Server(factory=factory)
    #     server.serve()

    #     client = Client(factory=factory)
    #     client.connect()

    #     client2 = Client(factory=factory)
    #     client2.connect()

    #     data_sample_key = client.register(SampleData())

    #     #Waiting for server to receive the datas
    #     time.sleep(1)

    #     #Check if the server receive them
    #     self.assertNotEqual(client2._rep_store[data_sample_key],None)

    



if __name__ == '__main__':
    unittest.main()