import unittest
import io
import json
import uuid
import random
from skills.extractor_tool_1790411035 import ExtractorTool1790411035, MetadataExtractionError
from unittest.mock import MagicMock
from skills import db_storage
from skills import market_parser

class TestExtractorTool1790411035Integration(unittest.TestCase):

    def setUp(self):
        self.extractor = ExtractorTool1790411035()
        self.storage_data = {}
        self.db = MagicMock()
        self.db.save.side_effect = lambda key, val: self.storage_data.update({key: val})
        self.db.load.side_effect = lambda key: self.storage_data.get(key)
        self.extractor.db_storage = self.db
        self.random_id = str(uuid.uuid4())
        self.random_value = random.randint(1000, 99999)

    def test_integration_stream_parsing_and_persistence(self):
        html_content = f"<html><body><div id='{self.random_id}' data-val='{self.random_value}'>Test</div></body></html>"
        stream = io.BytesIO(html_content.encode('utf-8'))

        parsed_result = self.extractor.parse_stream(stream)

        self.assertIn('div', parsed_result)
        self.assertEqual(parsed_result['div']['id'], self.random_id)
        self.assertEqual(int(parsed_result['div']['data-val']), self.random_value)

        self.extractor.persist_metadata(self.random_id, parsed_result)

        retrieved_data = self.db.load(self.random_id) if hasattr(self.db, 'load') else None
        if retrieved_data is not None:
            self.assertEqual(retrieved_data['div']['id'], self.random_id)

    def test_integration_json_stream_with_anomaly_check(self):
        test_payload = {
            "metric": "price",
            "value": self.random_value,
            "session_id": self.random_id
        }
        json_data = json.dumps(test_payload)
        stream = io.BytesIO(json_data.encode('utf-8'))

        processed_data = self.extractor.process_stream_with_anomaly_check(stream)

        self.assertIn('anomaly_detected', processed_data)
        self.assertEqual(processed_data['session_id'], self.random_id)
        self.assertEqual(processed_data['value'], self.random_value)

    def test_integration_error_handling_on_invalid_stream(self):
        invalid_stream = io.BytesIO(b"")
        invalid_stream.read = lambda: (_ for _ in ()).throw(Exception("Stream read error"))

        with self.assertRaises(MetadataExtractionError):
            self.extractor.parse_stream(invalid_stream)

if __name__ == '__main__':
    unittest.main()