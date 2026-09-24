import unittest
import uuid
import random
import os
from skills.extractor_tool_1790270493 import extractor_tool_1790270493
from skills.db_storage import db_storage
from skills.extractor_tool_1790087207 import extractor_tool_1790087207
from skills.extractor_tool_1790102839 import extractor_tool_1790102839
from skills.extractor_tool_1790262909 import extractor_tool_1790262909

class TestIntegrationExtractorTool1790270493(unittest.TestCase):
    def test_metadata_extraction_pipeline_integration(self):
        unique_id = str(uuid.uuid4())
        random_value = random.randint(10000, 99999)
        test_markup = f"<div id='{unique_id}' data-metric='{random_value}'>Test Markup Content</div>"

        raw_meta_1 = extractor_tool_1790087207(test_markup)
        raw_meta_2 = extractor_tool_1790102839(test_markup)
        preprocessed_data = extractor_tool_1790262909(raw_meta_1, raw_meta_2)

        final_extracted_metadata = extractor_tool_1790270493(test_markup, preprocessed_data)

        self.assertIsInstance(final_extracted_metadata, dict)
        self.assertIn("extracted_id", final_extracted_metadata)
        self.assertEqual(str(final_extracted_metadata["extracted_id"]), unique_id)
        self.assertIn("metric_value", final_extracted_metadata)
        self.assertEqual(int(final_extracted_metadata["metric_value"]), random_value)

        db_storage(final_extracted_metadata)

        file_path = f"data_{unique_id}.json"
        if os.path.exists(file_path):
            os.remove(file_path)

if __name__ == "__main__":
    unittest.main()