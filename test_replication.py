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

class TestData(unittest.TestCase):
    def setUp(self):
        self.map = {}
        self.client_api = Client()
        self.server_api = Server()

    def test_server_launching(self):
        self.server_api.serve()
        time.sleep(1)
        self.assertEqual(self.server_api.state(),1)

    def test_setup_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        data_sample = SampleData()
        rep_sample =  factory.construct(data_sample)(owner="toto")
        self.assertEqual(isinstance(rep_sample,RepSampleData), True)

    def test_client_connect(self):
        self.client_api.connect()
        time.sleep(1)
        self.assertEqual(self.client_api.state(),1)
    
    def test_client_stop(self):
        self.client_api.stop()
        time.sleep(1)
        self.assertEqual(self.client_api.state(),0)

    def test_client_add_rep(self):
        pass
    


    def test_add_replicated_value(self):
        pass

 
    



if __name__ == '__main__':
    unittest.main()