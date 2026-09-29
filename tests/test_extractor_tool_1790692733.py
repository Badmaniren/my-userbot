import unittest
from unittest.mock import patch
import uuid
import random
import string
from skills.extractor_tool_1790692733 import extractor_tool_1790692733

class TestExtractorTool1790692733(unittest.TestCase):

    def test_extractor_tool_1790692733_execution(self):
        run_id = uuid.uuid4().hex
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        markup = ''.join(random.choices(string.ascii_letters, k=25))
        entity = ''.join(random.choices(string.ascii_uppercase, k=5))
        sentiment_val = round(random.uniform(-1.0, 1.0), 2)

        payload = {
            "unique_run_id": run_id,
            "metric": metric_name,
            "source_markup": markup,
            "parsed_entity": entity,
            "sentiment": sentiment_val
        }

        result = extractor_tool_1790692733(payload)

        self.assertIn("metadata", result)
        self.assertIn("unique_run_id", result)
        self.assertIn("metric", result)

        self.assertEqual(result["unique_run_id"], run_id)
        self.assertEqual(result["metric"], metric_name)

        metadata = result["metadata"]
        self.assertEqual(metadata["source_markup"], markup)
        self.assertEqual(metadata["parsed_entity"], entity)
        self.assertEqual(metadata["sentiment"], sentiment_val)
        self.assertEqual(metadata["status"], "extracted")

    def test_extractor_tool_1790692733_missing_fields(self):
        payload = {}
        result = extractor_tool_1790692733(payload)

        self.assertIn("metadata", result)
        self.assertIsNone(result["unique_run_id"])
        self.assertIsNone(result["metric"])

        metadata = result["metadata"]
        self.assertIsNone(metadata["source_markup"])
        self.assertIsNone(metadata["parsed_entity"])
        self.assertIsNone(metadata["sentiment"])
        self.assertEqual(metadata["status"], "extracted")

if __name__ == "__main__":
    unittest.main()