import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string
import requests
from skills.extractor_tool_1790411035 import (
    ExtractorTool1790411035,
    MetadataExtractionError,
    extractor_tool_1790411035
)

class TestExtractorTool1790411035(unittest.TestCase):

    def setUp(self):
        self.tool = ExtractorTool1790411035()
        self.rand_str = uuid.uuid4().hex
        self.rand_key = "tag_" + uuid.uuid4().hex[:8]
        self.rand_val = uuid.uuid4().hex[:8]

    def test_parse_stream_success(self):
        html_content = f"<{self.rand_key} {self.rand_key}='{self.rand_val}'>Test</{self.rand_key}>".encode('utf-8')
        stream = io.BytesIO(html_content)
        result = self.tool.parse_stream(stream)
        self.assertIsInstance(result, dict)
        self.assertIn(self.rand_key, result)
        self.assertEqual(result[self.rand_key][self.rand_key], self.rand_val)

    def test_parse_stream_exception(self):
        mock_stream = MagicMock()
        mock_stream.read.side_effect = Exception(self.rand_str)
        with self.assertRaises(MetadataExtractionError) as ctx:
            self.tool.parse_stream(mock_stream)
        self.assertIn(self.rand_str, str(ctx.exception))

    def test_parse_stream_metadata_extraction_error_passthrough(self):
        mock_stream = MagicMock()
        mock_stream.read.side_effect = MetadataExtractionError(self.rand_str)
        with self.assertRaises(MetadataExtractionError) as ctx:
            self.tool.parse_stream(mock_stream)
        self.assertEqual(str(ctx.exception), self.rand_str)

    @patch('skills.extractor_tool_1790411035.requests.get')
    def test_extract_from_url(self, mock_get):
        url = f"https://{self.rand_str}.com/{uuid.uuid4().hex}"
        html_content = f"<div id='{self.rand_key}'></div>".encode('utf-8')
        mock_response = MagicMock()
        mock_response.content = html_content
        mock_get.return_value = mock_response

        result = self.tool.extract_from_url(url)
        mock_get.assert_called_once_with(url)
        self.assertIn('div', result)
        self.assertEqual(result['div']['id'], self.rand_key)

    def test_persist_metadata_with_storage(self):
        mock_db = MagicMock()
        self.tool.db_storage = mock_db
        record_id = random.randint(1, 100000)
        payload = {self.rand_key: self.rand_val}

        self.tool.persist_metadata(record_id, payload)
        mock_db.save.assert_called_once_with(record_id, payload)

    def test_persist_metadata_without_storage(self):
        self.tool.db_storage = None
        record_id = random.randint(1, 100000)
        payload = {self.rand_key: self.rand_val}
        try:
            self.tool.persist_metadata(record_id, payload)
        except Exception as e:
            self.fail(f"persist_metadata raised exception without db_storage: {e}")

    def test_process_stream_with_anomaly_check_dict(self):
        data_dict = {self.rand_key: self.rand_val}
        stream = io.BytesIO(json.dumps(data_dict).encode('utf-8'))

        mock_anomaly = MagicMock()
        mock_anomaly.check.return_value = True
        self.tool.market_anomaly_detector = mock_anomaly

        res = self.tool.process_stream_with_anomaly_check(stream)
        mock_anomaly.check.assert_called_once()
        self.assertIsInstance(res, dict)
        self.assertEqual(res[self.rand_key], self.rand_val)
        self.assertTrue(res['anomaly_detected'])

    def test_process_stream_with_anomaly_check_non_dict(self):
        data_list = [self.rand_str, random.randint(1, 100)]
        stream = io.BytesIO(json.dumps(data_list).encode('utf-8'))

        mock_anomaly = MagicMock()
        mock_anomaly.check.return_value = False
        self.tool.market_anomaly_detector = mock_anomaly

        res = self.tool.process_stream_with_anomaly_check(stream)
        mock_anomaly.check.assert_called_once()
        self.assertIsInstance(res, dict)
        self.assertEqual(res['data'], data_list)
        self.assertFalse(res['anomaly_detected'])

    def test_extractor_tool_helper_dict(self):
        input_dict = {self.rand_key: self.rand_val}
        res = extractor_tool_1790411035(input_dict)
        self.assertEqual(res, input_dict)

    def test_extractor_tool_helper_non_dict(self):
        input_val = ''.join(random.choices(string.ascii_letters, k=10))
        res = extractor_tool_1790411035(input_val)
        self.assertEqual(res, {"metadata": {}})