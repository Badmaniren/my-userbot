import unittest
from unittest.mock import patch
import uuid
import random
import string

from skills.anomaly_pattern_analyzer import anomaly_filter


class TestAnomalyPatternAnalyzerFilter(unittest.TestCase):

    def test_start_new_with_valid_structured_data(self):
        rand_prefix = "".join(random.choices(string.ascii_lowercase, k=8))
        rand_key = f"{rand_prefix}_{uuid.uuid4().hex}"
        rand_value = random.randint(1000, 99999)
        
        input_data = {
            rand_key: rand_value,
            "status": "active",
            "metadata": uuid.uuid4().hex
        }
        
        result = anomaly_filter.start_new(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("filtered_data", result)
        self.assertEqual(result["filtered_data"][rand_key], rand_value)
        self.assertEqual(result["status"], "processed")

    def test_start_new_with_chaos_payload(self):
        rand_text = uuid.uuid4().hex
        rand_list_len = random.randint(3, 10)
        rand_list = [uuid.uuid4().hex for _ in range(rand_list_len)]
        
        input_data = {
            "payload": rand_text,
            "items": rand_list,
            "error_code": random.randint(400, 599)
        }
        
        result = anomaly_filter.start_new(input_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("filtered_data", result)
        self.assertEqual(result["filtered_data"]["payload"], rand_text)
        self.assertEqual(result["filtered_data"]["items"], rand_list)

    def test_start_new_empty_or_malformed_input(self):
        malformed_inputs = [
            {},
            None,
            [],
            uuid.uuid4().hex
        ]
        
        for bad_input in malformed_inputs:
            with self.subTest(bad_input=bad_input):
                try:
                    result = anomaly_filter.start_new(bad_input)
                    self.assertIsInstance(result, dict)
                    self.assertIn("status", result)
                except Exception as e:
                    self.assertIsInstance(e, (ValueError, TypeError, KeyError))


if __name__ == "__main__":
    unittest.main()