import cProfile
import logging
import re
import time
import unittest

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)
logger = logging.getLogger(__name__)


from replication import ReplicatedDatablock, ReplicatedDataFactory
from replication_client import Client, Server


class SampleData():
    def __init__(self, map={"sample": "data"}):
        self.map = map


class RepSampleData(ReplicatedDatablock):
    def serialize(self, data):
        import pickle

        return pickle.dumps(data)

    def deserialize(self, data):
        import pickle

        return pickle.loads(data)

    def dump(self):
        import json
        output = {}
        output['map'] = json.dumps(self.pointer.map)
        return output

    def load(self, target=None):
        import json
        if target is None:
            target = SampleData()

        target.map = json.loads(self.buffer['map'])


class TestDataFactory(unittest.TestCase):
    def test_data_factory(self):
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)
        data_sample = SampleData()
        rep_sample = factory.construct_from_dcc(
            data_sample)(owner="toto", pointer=data_sample)

        self.assertEqual(isinstance(rep_sample, RepSampleData), True)


class TestClient(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName)

    def test_empty_snapshot(self):
        # Setup
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        client = Client(factory=factory)

        server.serve(port=5570)
        client.connect(port=5570, id="client_test_callback")

        test_state = client.state

        server.stop()
        client.disconnect()

        self.assertNotEqual(test_state, 2)

    def test_filled_snapshot(self):
        # Setup
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        client = Client(factory=factory)
        client2 = Client(factory=factory)

        server.serve(port=5575)
        client.connect(port=5575,id="cli_test_filled_snapshot")

        # Test the key registering
        data_sample_key = client.register(SampleData())

        client2.connect(port=5575, id="client_2")
        time.sleep(0.2)
        rep_test_key = client2._rep_store[data_sample_key].uuid

        server.stop()
        client.disconnect()
        client2.disconnect()

        self.assertEqual(data_sample_key, rep_test_key)

    def test_register_client_data(self):
        # Setup environment

        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        server.serve(port=5560)

        client = Client(factory=factory)
        client.connect(port=5560,id="cli_test_register_client_data")

        client2 = Client(factory=factory)
        client2.connect(port=5560, id="cli2_test_register_client_data")

        # Test the key registering
        data_sample_key = client.register(SampleData())

        time.sleep(0.3)
        # Waiting for server to receive the datas
        rep_test_key = client2._rep_store[data_sample_key].uuid

        client.disconnect()
        client2.disconnect()
        server.stop()

        self.assertEqual(rep_test_key, data_sample_key)

    def test_client_data_intergity(self):
        # Setup environment
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        server.serve(port=5560)

        client = Client(factory=factory)
        client.connect(port=5560, id="cli_test_client_data_intergity")

        client2 = Client(factory=factory)
        client2.connect(port=5560, id="cli2_test_client_data_intergity")

        test_map = {"toto": "test"}
        # Test the key registering
        data_sample_key = client.register(SampleData(map=test_map))

        test_map_result = SampleData()
        # Waiting for server to receive the datas
        time.sleep(1)

        client2._rep_store[data_sample_key].load(target=test_map_result)

        client.disconnect()
        client2.disconnect()
        server.stop()

        self.assertEqual(test_map_result.map["toto"], test_map["toto"])

    def test_client_unregister_key(self):
        # Setup environment
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        server.serve(port=5560)

        client = Client(factory=factory)
        client.connect(port=5560, id="cli_test_client_data_intergity")

        client2 = Client(factory=factory)
        client2.connect(port=5560, id="cli2_test_client_data_intergity")

        test_map = {"toto": "test"}
        # Test the key registering
        data_sample_key = client.register(SampleData(map=test_map))

        test_map_result = SampleData()

        # Waiting for server to receive the datas
        time.sleep(.1)

        client2._rep_store[data_sample_key].load(target=test_map_result)

        client.unregister(data_sample_key)
        time.sleep(.1)

        logger.debug("client store:")
        logger.debug(client._rep_store)
        logger.debug("client2 store:")
        logger.debug(client2._rep_store)
        logger.debug("server store:")
        logger.debug(server._rep_store)

        client.disconnect()
        client2.disconnect()
        server.stop()

        self.assertFalse(data_sample_key in client._rep_store)

    def test_client_disconnect(self):
        pass

    def test_client_change_rights(self):
        pass


class TestStressClient(unittest.TestCase):
    def test_stress_register(self):
        total_time = 0
     # Setup
        factory = ReplicatedDataFactory()
        factory.register_type(SampleData, RepSampleData)

        server = Server(factory=factory)
        client = Client(factory=factory)
        client2 = Client(factory=factory)

        server.serve(port=5575)
        client.connect(port=5575,id="cli_test_filled_snapshot")
        client2.connect(port=5575,id="client_2")

        # Test the key registering
        for i in range(10000):
            client.register(SampleData())

        while len(client2._rep_store.keys()) < 10000:
            time.sleep(0.00001)
            total_time += 0.00001

        # test_num_items = len(client2._rep_store.keys())
        server.stop()
        client.disconnect()
        client2.disconnect()
        logger.info("{} s for 10000 values".format(total_time))

        self.assertLess(total_time, 1)


def suite():
    suite = unittest.TestSuite()

    # Data factory
    suite.addTest(TestDataFactory('test_data_factory'))

    # Client
    suite.addTest(TestClient('test_empty_snapshot'))
    suite.addTest(TestClient('test_filled_snapshot'))
    suite.addTest(TestClient('test_register_client_data'))
    suite.addTest(TestClient('test_client_data_intergity'))

    # Stress test
    suite.addTest(TestStressClient('test_stress_register'))

    return suite


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
