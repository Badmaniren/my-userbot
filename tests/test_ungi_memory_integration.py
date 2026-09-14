import unittest
from skills.ungi_memory import UngiMemory

class TestUngiMemoryIntegration(unittest.TestCase):
    def test_ungi_memory_integration_flow(self):
        memory = UngiMemory()

        test_key = "integration_test_key"
        test_value = "integration_test_value"

        store_result: bool = memory.store(test_key, test_value)
        self.assertIsInstance(store_result, bool)
        self.assertTrue(store_result)

        retrieve_result: str = memory.retrieve(test_key)
        self.assertIsInstance(retrieve_result, str)
        self.assertEqual(retrieve_result, test_value)

        exists_result: bool = memory.exists(test_key)
        self.assertIsInstance(exists_result, bool)
        self.assertTrue(exists_result)

        delete_result: bool = memory.delete(test_key)
        self.assertIsInstance(delete_result, bool)
        self.assertTrue(delete_result)

        final_exists_result: bool = memory.exists(test_key)
        self.assertIsInstance(final_exists_result, bool)
        self.assertFalse(final_exists_result)
