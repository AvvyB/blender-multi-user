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

        return pickle.loads(data)


class TestDataFactory(unittest.TestCase):
    def test_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)
        data_sample = SampleData()
        rep_sample = factory.construct_from_dcc(data_sample)(owner="toto", data=data_sample)
        
        self.assertEqual(isinstance(rep_sample,RepSampleData), True)


class TestClient(unittest.TestCase):
    def __init__(self,methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)

    def test_empty_snapshot(self):
        # Setup
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        client = Client(factory=factory, id="client_test_callback")

        server.serve(port=5570)
        client.connect(port=5570)

        test_state = client.state
        
        server.stop()
        client.disconnect()

        self.assertNotEqual(test_state, 2)


    def test_register_client_data(self):
        # Setup environment
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        server.serve(port=5560)

        client = Client(factory=factory, id="client_1")
        client.connect(port=5560)

        client2 = Client(factory=factory, id="client_2")
        client2.connect(port=5560)
       
        # Test the key registering
        data_sample_key = client.register(SampleData())

        #Waiting for server to receive the datas
        time.sleep(.5)

        rep_test_key = client2._rep_store[data_sample_key].uuid

        
        client.disconnect()
        client2.disconnect()
        server.stop()


        self.assertEqual(rep_test_key, data_sample_key)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(TestDataFactory('test_data_factory'))
    suite.addTest(TestClient('test_empty_snapshot'))
    suite.addTest(TestClient('test_register_client_data'))

    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(failfast=True,verbosity=2)
    runner.run(suite())