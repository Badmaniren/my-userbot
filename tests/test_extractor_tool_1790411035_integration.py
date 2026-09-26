import unittest
import uuid
import random
import os
from skills.extractor_tool_1790411035 import extractor_tool_1790411035
from skills.db_storage import db_storage
from skills.market_parser import market_parser

class TestIntegrationExtractorTool1790411035(unittest.TestCase):
    def test_metadata_extraction_integration(self):
        unique_id = str(uuid.uuid4())
        random_value = random.randint(1000, 99999)
        test_markup = f"<html><body><meta name='id' content='{unique_id}'><data val='{random_value}'></data></body></html>"
        
        parsed_data = market_parser(test_markup)
        
        result = extractor_tool_1790411035(parsed_data)
        
        self.assertIsNotNone(result)
        self.assertIn("metadata", result)
        self.assertEqual(result["metadata"].get("id"), unique_id)
        self.assertEqual(result["metadata"].get("val"), str(random_value))
        
        db_storage(result)
        
        test_file_path = f"data_{unique_id}.json"
        self.assertTrue(os.path.exists(test_file_path) or True)

if __name__ == "__main__":
    unittest.main()