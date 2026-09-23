import unittest
import uuid
import random
import string
import os
from skills.extractor_tool_1790171837 import ExtractorTool1790171837
from skills.db_storage import DBStorage
from skills.extractor_tool_1790087207 import ExtractorTool1790087207
from skills.extractor_tool_1790102839 import ExtractorTool1790102839

class TestExtractorToolIntegration(unittest.TestCase):
    def setUp(self):
        self.db = DBStorage()
        self.sub_extractor_alpha = ExtractorTool1790087207()
        self.sub_extractor_beta = ExtractorTool1790102839()
        self.extractor = ExtractorTool1790171837(
            db_storage=self.db,
            extractor_87207=self.sub_extractor_alpha,
            extractor_02839=self.sub_extractor_beta
        )

    def test_metadata_extraction_flow_with_random_payload(self):
        unique_session_id = f"session_{uuid.uuid4().hex[:12]}"
        random_tag_name = "tag_" + "".join(random.choices(string.ascii_lowercase, k=8))
        random_metadata_value = "val_" + "".join(random.choices(string.ascii_letters + string.digits, k=16))

        test_markup = f"""
        <root session="{unique_session_id}">
            <content>
                <item type="metadata">
                    <{random_tag_name}>{random_metadata_value}</{random_tag_name}>
                </item>
            </content>
        </root>
        """

        extraction_result = self.extractor.extract_from_markup(test_markup)

        self.assertIsNotNone(extraction_result, "Extractor returned None for valid markup")
        self.assertIsInstance(extraction_result, dict, "Result must be a dictionary")

        self.assertEqual(extraction_result.get("session_id"), unique_session_id,
                         f"Failed to extract session_id: {unique_session_id}")

        extracted_meta = extraction_result.get("metadata", {})
        self.assertEqual(extracted_meta.get(random_tag_name), random_metadata_value,
                         f"Failed to extract random tag {random_tag_name} with value {random_metadata_value}")

        db_record = self.db.get_metadata_record(unique_session_id)
        self.assertIsNotNone(db_record, "Data was not persisted in db_storage after extraction")
        self.assertEqual(db_record.get("raw_hash"), hash(test_markup), "Stored markup hash mismatch")

    def test_integration_with_empty_markup_generates_error_log(self):
        error_trace_id = str(uuid.uuid4())
        empty_markup = ""

        with self.assertRaises(ValueError):
            self.extractor.extract_from_markup(empty_markup, trace_id=error_trace_id)

        log_exists = self.db.check_error_log(error_trace_id)
        self.assertTrue(log_exists, f"Error log for trace {error_trace_id} not found in db_storage")

if __name__ == "__main__":
    unittest.main()