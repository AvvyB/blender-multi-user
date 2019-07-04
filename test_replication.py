import unittest
import replication

class TestData(unittest.TestCase):
    def setUp(self):
        self.map = {}
        self.sample_data = replication.ReplicatedDatablock(owner="toto")

    def test_create_replicated_data(self):
        self.assertNotEqual(self.sample_data.uuid,None)        
    
    def test_push_replicated_data(self):
        pass

if __name__ == '__main__':
    unittest.main()