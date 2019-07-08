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


# class TestClient(unittest.TestCase):
#     def setUp(self):
#         factory = ReplicatedDataFactory()
#         self.client_api = Client(factory=factory)

#     def test_client_connect(self):
#         self.client_api.connect()
#         time.sleep(1)
#         self.assertEqual(self.client_api._net.state,1)
        

#     def test_client_disconnect(self):
#         self.client_api.disconnect()
#         time.sleep(1)
#         self.assertEqual(self.client_api._net.state,0)



class TestDataReplication(unittest.TestCase):
    # def test_server_launching(self):
    #     log.info("test_server_launching")
    #     self.server_api.serve()
    #     time.sleep(1)
    #     self.assertEqual(self.server_api.state(),1)

    # def test_server_stop(self):
    #     log.info("test_server_launching")
    #     self.server_api.stop()
    #     time.sleep(1)
    #     self.assertEqual(self.server_api.state(),0)

    def test_setup_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)
        data_sample = SampleData()
        rep_sample = factory.construct(data_sample)(owner="toto")
        
        self.assertEqual(isinstance(rep_sample,RepSampleData), True)

    def test_replicate_client_data(self):        
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server_api = Server()
        server_api.serve()
        client_api = Client(factory=factory)
        client_api.connect()

        data_sample = SampleData()
        data_sample_key = client_api.add(data_sample)

        
        self.assertNotEqual(client_api._rep_store[data_sample_key],None)

    



if __name__ == '__main__':
    unittest.main()