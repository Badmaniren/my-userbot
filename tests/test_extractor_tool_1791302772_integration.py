import unittest
import uuid
import random
from skills.market_parser import market_parser
from skills.extractor_tool_1791302772 import extractor_tool_1791302772

try:
    from skills.db_storage import db_storage
except ImportError:
    db_storage = None

class TestIntegrationExtractorTool1791302772(unittest.TestCase):
    def test_integration_pipeline_with_real_market_parser(self):
        unique_id = str(uuid.uuid4())
        random_value = random.randint(1000, 99999)

        raw_payload = {
            "test_id": unique_id,
            "metric": random_value,
            "source": "integration_test"
        }

        parsed_data = market_parser(raw_payload)

        result = extractor_tool_1791302772(parsed_data)

        self.assertIsInstance(result, dict)
        self.assertIn("test_id", result)
        self.assertEqual(result["test_id"], unique_id)
        self.assertIn("metric", result)
        self.assertEqual(result["metric"], random_value)
        self.assertEqual(result.get("source"), "integration_test")

        if db_storage is not None and hasattr(db_storage, "save"):
            db_storage.save(result)

if __name__ == "__main__":
    unittest.main()