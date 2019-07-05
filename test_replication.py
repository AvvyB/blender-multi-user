import unittest
from replication import ReplicatedDatablock, ReplicatedDataFactory
import umsgpack
import logging
from replication_client import Client


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
    def test_setup_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

    def test_run_client(self):
        self.client_api.connect()
    
    def test_stop_client(self):
        self.client_api.stop()

    def test_add_replicated_value(self):
        pass

    def test_create_replicated_data(self):
        self.assertNotEqual(self.sample_data.uuid,None)        
    
    



if __name__ == '__main__':
    unittest.main()